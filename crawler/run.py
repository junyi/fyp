#!/usr/bin/env python

import os
from twisted.internet import reactor
from scrapy.crawler import Crawler
from scrapy import log, signals
from crawler.spiders.jobsbank import JobsBankSpider
from scrapy.utils.project import get_project_settings

retry_count = 0

def on_spider_closed():
	retry_count += 1
	if os.path.isfile("session.p") and retry_count < 5:
		main()
	else:
		return

def main():
	if os.path.isfile("session.p"):
		data = pickle.load(open("session.p", "rb"))
		try:
			current_page = data["current_page"]
			total = data["total"]
		except Exception:
			current_page = 1
	else:
		current_page = 1

	spider = JobsBankSpider(current_page=current_page, retry_count=retry_count)
	settings = get_project_settings()
	crawler = Crawler(settings)
	crawler.signals.connect(reactor.stop, signal=signals.spider_closed)
	crawler.signals.connect(on_spider_closed, signal=signals.spider_closed)
	crawler.configure()
	crawler.crawl(spider)
	crawler.start()
	log.start()
	reactor.run() # the script will block here until the spider_closed signal was sent

if __name__ == '__main__':
	main()