from crawler.items import JobsBankItem
from crawler.utils import DEBUG, INFO, WARNING, ERROR
from scrapy import FormRequest, Request, signals
from scrapy.selector import Selector
from scrapy.spider import Spider
from scrapy.http import TextResponse
from scrapy.xlib.pydispatch import dispatcher
from html2text import html2text

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException

from urllib2 import URLError

# import pdb
import sys
import os
import nltk
import demjson
import pickle
import traceback
import signal

CUR_DIR = os.path.dirname(os.path.abspath(__file__))
SESSION_P = os.path.join(CUR_DIR, "..", "session.p")

class JobsBankSpider(Spider):
    name = "jobsbank"
    allowed_domains = ["www.jobsbank.gov.sg"]
    start_urls = []
    current_page = 1
    stop_page = -1
    total_no_of_pages = -1
    stop = False

    def __init__(self, current_page=1, retry_count=0, stop_page=-1):
        INFO("Current retry count at %d" % retry_count)

        self.current_page = current_page
        self.stop_page = stop_page

        if self.stop_page != -1 and self.current_page >= self.stop_page:
            INFO("current_page >= stop_page: %d > %d" % (self.current_page, self.stop_page))
            INFO("Resetting current_page to 1")
            self.current_page = 1
            self.save_state()
        
        dispatcher.connect(self.spider_closed, signals.spider_closed)

    def spider_closed(self, spider): 
        if spider is not self:
            return

    def start_requests(self):
        return [
            FormRequest("https://www.jobsbank.gov.sg/ICMSPortal/portlets/JobBankHandler/SearchResult.do",
                        formdata={
                            '{actionForm.currentPageNumber}': str(self.current_page),
                            '{actionForm.checkValidRequest}': 'YES',
                            '{actionForm.recordsPerPage}': '10'},  # Multiply by 5 to get the actual no of records
                        method="POST",
                        callback=self.parse_page)]

    def save_state(self):
        INFO("Storing current_page at page %s/%s" % (self.current_page, self.total_no_of_pages))
        data = {
            'current_page': self.current_page,
            'stop_page': self.stop_page,
            'total': self.total_no_of_pages
        }
        pickle.dump(data, open(SESSION_P, "wb"))

    def parse_page(self, response):
        if self.stop:
            INFO("Received stop signal: stopped parsing")
            self.save_state()

            return

        sel = Selector(response)
        if self.total_no_of_pages == -1:
            total = sel.xpath("//input[@id='totalPageNum']/@value").extract()[0].strip()
            self.total_no_of_pages = int(total)
            INFO(self.total_no_of_pages)

        jobs = sel.xpath("//article")

        for job in jobs:
            item = JobsBankItem()
            locations = job.xpath(
                ".//td[@class='location']/div/p/@title").extract()[0].split('|')
            locations = [l.strip() for l in locations]

            title = job.xpath(
                ".//td[@class='jobDesActive']/a[@class='text']/text()").extract()[0]

            item["jobId"] = title[title.index("ID:") + 3: title.rfind(")")]
            DEBUG(item["jobId"])
            item["locations"] = locations

            job_detail_link = "https://www.jobsbank.gov.sg" + job.xpath(
                ".//td[@class='jobDesActive']/a/@href").extract()[0]
            item["url"] = job_detail_link

            request = Request(job_detail_link, callback=self.parse_job, priority=1)
            request.meta['item'] = item
            request.meta['retryCount'] = 0
            yield request

        if self.current_page < self.total_no_of_pages and (self.stop_page == -1 or self.current_page < self.stop_page):
            INFO("Done scraping page %d/%d" %
                    (self.current_page, self.total_no_of_pages))
            self.current_page += 1
            self.save_state()
            yield FormRequest("https://www.jobsbank.gov.sg/ICMSPortal/portlets/JobBankHandler/SearchResult3.do",
                               priority=5,
                               formdata={
                                   '{actionForm.currentPageNumber}': str(self.current_page),
                                   '{actionForm.checkValidRequest}': 'YES',
                                   '{actionForm.recordsPerPage}': '10',  # Multiply by 5 to get the actual no of records
                                   '{actionForm.searchType}': 'Quick Search'},
                               method="POST",
                               callback=self.parse_page)
        else:
            if self.stop_page != -1:
                INFO("Reached stop_page at %d, Done scraping page %d/%d" %
                    (self.stop_page, self.current_page, self.total_no_of_pages))
                return
           
            INFO("Done scraping page %d/%d" %
                    (self.current_page, self.total_no_of_pages))
            INFO("Finished scraping")
            if os.path.isfile(SESSION_P):
                data = pickle.load(open(SESSION_P, "rb"))
                if data["current_page"] < self.current_page:
                    os.remove(SESSION_P)
                    INFO("Removing obsolete session file")
            return

    def parse_job(self, response):
        try:
            self.driver = webdriver.PhantomJS('/usr/bin/phantomjs', service_args=['--ssl-protocol=any'])
            self.driver.get(response.url)
        except URLError, e:
            ERROR("Connection error for job %s" % response.meta['item']['jobId'])
            self.stop = True
            return

        # a bug in phantomjs: hang randomly
        # http://code.google.com/p/phantomjs/issues/detail?id=652
        timelimit = 10
        handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timelimit)

        try:
            try:
                wait = WebDriverWait(self.driver, 10)
                wait.until(lambda loaded: self.driver.execute_script("return document.readyState;") == "complete")
            except TimeoutException:
                traceback.print_exc(file=open("log/error.log","a"))
                self.driver.quit()
        except Exception:
            print "PhantomJS is running beyond {} seconds, restarting".format(timelimit)
            self.driver.quit()
            if sys.platform is not 'win32':
                os.system("killall phantomjs")
        finally:
            # reset the handler to the old one
            signal.signal(signal.SIGALRM, handler)

        # cancel the alarm
        signal.alarm(0)
            
        new_response = TextResponse(url=response.url, body=self.driver.page_source, encoding='utf-8')
        # pdb.set_trace()
        # self.driver.close()
        sel = Selector(new_response)
        # with open("response.txt", "w") as f:
        #     f.write(response.body_as_unicode())

        item = response.meta['item']
        # item = JobsBankItem()

        try:

            item["title"] = sel.xpath("//div[@class='jobDes']//h3/text()").extract()[0].strip()
            
            postingDate = sel.xpath("//div[@class='jobDes']//div/p/text()").extract()[0]
            item["postingDate"] = postingDate[postingDate.index(":") + 1:].strip()

            closingDate = sel.xpath("//div[@class='jobDes']//div/p/text()").extract()[1]
            item["closingDate"] = closingDate[closingDate.index(":") + 1:].strip()

            jobId = sel.xpath("//div[@class='jobDes']//div/p/text()").extract()[2]
            item["jobId"] = jobId.strip()

            description = sel.xpath("//div[@id='divMainJobDescription']").extract()
            item["description"] = ''.join([html2text(i) for i in description])

            requirements = sel.xpath("//div[@id='divMainSkillsRequired']").extract()
            item["requirements"] = ''.join([html2text(i) for i in requirements])

            categories = sel.xpath("//div[@class='jd_contentRight']/dl[1]//li/span/text()").extract()
            item["categories"] = [i.strip() for i in categories]

            item["industry"] = sel.xpath("//div[@class='jd_contentRight']/dl[2]//span/text()").extract()[0].strip()

            item["empType"] = sel.xpath("//div[@class='jd_contentRight']/ul[1]//li/span/text()").extract()

            item["workingHours"] = sel.xpath("//div[@class='jd_contentRight']/ul[2]//li/span/text()").extract()[0].strip()

            item["shiftPattern"] = sel.xpath("//div[@class='jd_contentRight']/ul[3]//li/span/text()").extract()[0].strip()

            salary = sel.xpath("//div[@class='jd_contentRight']/ul[4]//span/text()").extract()
            item["salary"] = ''.join([html2text(i) for i in salary]).strip().replace('\n', '')

            item["jobLevel"] = sel.xpath("//div[@class='jd_contentRight']/ul[5]//span/text()").extract()[0].strip()

            item["yearsOfExp"] = sel.xpath("//div[@class='jd_contentRight']/ul[6]//li/text()").extract()[0].strip()

            item["noOfVacancies"] = sel.xpath("//div[@class='jd_contentRight']/span[@class='text'][1]/text()").extract()[0].strip()

        except (IndexError, KeyError) as e:
            traceback.print_exc(file=open("log/error.log","a"))
        finally:
            self.driver.quit()

        #     WARNING("Failed to crawl %s, recrawling..." % item["jobId"])
        #     request = Request(response.url, callback=self.parse_job, dont_filter=True)
        #     request.meta['item'] = item
        #     request.meta['retryCount'] = response.meta['retryCount'] + 1

        #     if request.meta['retryCount'] > 5:
        #         ERROR("Failed to crawl %s after 5 times, abandoning..." % item["jobId"])
        #         return

        #     yield request
        #     return

        # with open("output.txt", "a") as f:
        #     f.write(demjson.encode(item)+"\n")

        yield item

def timeout_handler(signum, frame):
    raise Exception("Timeout!")
