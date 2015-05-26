#!/usr/bin/env python

import os
import pickle
from twisted.internet import reactor
from scrapy.crawler import Crawler
from scrapy import log, signals
from crawler.utils import DEBUG, INFO, WARNING, ERROR
from crawler.spiders.jobsbank import JobsBankSpider
from scrapy.utils.project import get_project_settings
from scrapy.utils.ossignal import install_shutdown_handlers, signal_names

CUR_DIR = os.path.dirname(os.path.abspath(__file__))
SESSION_P = os.path.join(CUR_DIR, "session.p")
retry_count = 0

def on_spider_closed():
    global retry_count
    retry_count += 1
    if os.path.isfile(SESSION_P) and retry_count < 5:
        os.execv(__file__, sys.argv) # Restart this script
    else:
        return

def main():
    global retry_count
    INFO("Running main: retry_count=%d" % retry_count)
    if os.path.isfile(SESSION_P):
        data = pickle.load(open(SESSION_P, "rb"))
        try:
            current_page = data["current_page"]
            total = data["total"]
            INFO("Found session.p")
            INFO("[session.p] current_page=%d" % current_page)

        except Exception:
            current_page = 1
    else:
        current_page = 1

    spider = JobsBankSpider(current_page=current_page, retry_count=retry_count)

    def handle_shutdown(signum, _):
        signame = signal_names[signum]
        INFO("Received %s, shutting down gracefully." % signame)

        if isinstance(spider, JobsBankSpider):
            INFO("Storing current_page at page %s/%s" % (spider.current_page, spider.total_no_of_pages))
            data = {
                'current_page': spider.current_page,
                'total': spider.total_no_of_pages
            }
            pickle.dump(data, open(SESSION_P, "wb"))

        if sys.platform is not 'win32':
            os.system("killall -9 phantomjs")

    install_shutdown_handlers(handle_shutdown)
    
    settings = get_project_settings()
    crawler = Crawler(settings)
    crawler.signals.connect(reactor.stop, signal=signals.spider_closed)
    crawler.signals.connect(on_spider_closed, signal=signals.spider_closed)
    crawler.configure()
    crawler.crawl(spider)
    crawler.start()

    LOG_FILE = settings['LOG_FILE']
    log.start(LOG_FILE, loglevel=log.INFO)
    reactor.run() # the script will block here until the spider_closed signal was sent

if __name__ == '__main__':
    main()