# -*- coding: utf-8 -*-
from scrapy.spiders import Spider
from scrapy.selector import Selector
from scrapy.http import FormRequest
from scrapy.http import Request
from gold_spider.items import GoldItem
import sys
import re
import threading
import logging
import random

class GoldSpider(Spider):
    user_agent = 'Mozilla/5.0 (Linux; Android 4.4.4; Nexus 5 Build/KTU84P) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.114 Mobile Safari/537.36'
    start_urls = ['http://movie.douban.com/tag']
    name = 'gold'

    _visited = set()
    _http_proxies = [
    ]

    def _get_next_proxy(self):
        proxy = random.choice(self._http_proxies)
        #proxy = 'http://127.0.0.1:8118'
        return proxy
    def _create_request(self, url, callback=None):
        request = Request(url, callback)
        #request.meta['proxy'] = self._get_next_proxy()
        return request

    def __init__(self):
        reload(sys)
        sys.setdefaultencoding('utf-8')

    def start_requests(self):
        for url in self.start_urls:
            request = self._create_request(url)
            yield request

    def parse_one_movie(self, response):
        selector = Selector(response)
        title = selector.css("div.ckdSubject h1.ckd-content").xpath("text()").extract()[0]
        rate_text = selector.css("div.movie-info div.movie-rating span.rating_num").xpath("text()").extract()
        rate = 'n/a' if not rate_text else rate_text[0]

        content_list = selector.css("div#full-summary p span.ckd-content").xpath("text()").extract()
        content = ",".join(content_list)
        span = selector.css("div.movie-info p.ckd-content span[property$=genre]").xpath("text()").extract()
        genre = ",".join(span)
        item = self._build_item(title, rate, genre, content)
        return item

    def _build_item(self, title, rate, genre, content):
        item = GoldItem();
        item['title'] = title;
        item['rate'] = rate;
        item['genre'] = genre;
        item['content'] = content;
        return item

    def parse_tag(self, response):
        selector = Selector(response)
        response_url = response.url
        pl2 = selector.css("div.pl2")

        for div in pl2:
            href = div.css("a.ckd-title ::attr(href)").extract()[0]
            if self._not_visited(href):
                request = self._create_request(href, callback=self.parse_one_movie)
                yield request

        next_page = selector.css("div.paginator span.next a::attr(href)").extract()
        if next_page:
            request = self._create_request(next_page[0], callback=self.parse_tag)
            yield request

    def _not_visited(self, link):
        if not link in self._visited:
            self._visited.add(link)
            return True
        return False

    def parse(self, response):
        response_url =  response.url
        selector = Selector(response)
        all_link = selector.xpath(u"//div[span/text() = '类型']/a")
        for a in all_link:
            link = a.css("::attr(href)").extract()[0]
            link = response_url + link[2:]
            request = self._create_request(link, callback=self.parse_tag)
            yield request
