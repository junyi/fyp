from crawler.items import JobsBankItem
from crawler.utils import DEBUG, INFO, WARNING, ERROR
from scrapy import FormRequest, Request
from scrapy.selector import Selector
from scrapy.spider import Spider
from scrapy.http import TextResponse 
from html2text import html2text

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait

from urllib2 import URLError

# import pdb
import os
import nltk
import demjson
import pickle
import traceback

class JobsBankSpider(Spider):
    name = "jobsbank"
    allowed_domains = ["www.jobsbank.gov.sg"]
    start_urls = []
    current_page = 1
    total_no_of_pages = -1
    stop = False

    def __init__(self, current_page=1, retry_count=0):
        self.driver = webdriver.PhantomJS(service_args=['--ssl-protocol=any'])
        INFO("Current retry count at %d" % retry_count)
        self.current_page = current_page

    def start_requests(self):
        return [
            FormRequest("https://www.jobsbank.gov.sg/ICMSPortal/portlets/JobBankHandler/SearchResult.do",
                        formdata={
                            '{actionForm.currentPageNumber}': str(current_page),
                            '{actionForm.checkValidRequest}': 'YES',
                            '{actionForm.recordsPerPage}': '10'},  # Multiply by 5 to get the actual no of records
                        method="POST",
                        callback=self.parse_page)]

    def parse_page(self, response):
        if self.stop:
            INFO("Stopped parsing")
            INFO("Storing current_page at page %s/%s" % (self.current_page, self.total_no_of_pages))
            data = {
                'current_page': self.current_page,
                'total': self.total_no_of_pages
            }
            pickle.dump(data, open("session.p", "wb"))

            return

        sel = Selector(response)
        if self.total_no_of_pages == -1:
            total = sel.xpath("//input[@id='totalPageNum']/@value").extract()[0].strip()
            self.total_no_of_pages = int(total)
            INFO(self.total_no_of_pages)

        jobs = sel.xpath("//article")

        for job in jobs:
            item = JobsBankItem()
            location = job.xpath(
                ".//td[@class='location']/label/text()").extract()[0]
            title = job.xpath(
                ".//td[@class='jobDesActive']/a[@class='text']/text()").extract()[0]

            item["jobId"] = title[title.index("ID:") + 3: title.rfind(")")]
            DEBUG(item["jobId"])
            item["location"] = location

            job_detail_link = "https://www.jobsbank.gov.sg" + job.xpath(
                ".//td[@class='jobDesActive']/a/@href").extract()[0]
            item["url"] = job_detail_link

            request = Request(job_detail_link, callback=self.parse_job, priority=1)
            request.meta['item'] = item
            request.meta['retryCount'] = 0
            yield request

        if self.current_page < self.total_no_of_pages:
            INFO("Done scraping page %d/%d" %
                    (self.current_page, self.total_no_of_pages))
            self.current_page += 1
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
            INFO("Done scraping page %d/%d" %
                    (self.current_page, self.total_no_of_pages))
            INFO("Finished scraping")
            if os.path.isfile("session.p"):
                data = pickle.load(open("session.p", "rb"))
                if data["current_page"] < self.current_page:
                    os.remove("session.p")
                    INFO("Removing obsolete session file")
            return

    def parse_job(self, response):
        try:
            self.driver.get(response.url)
        except URLError, e:
            ERROR("Connection error for job %s" % response.meta['item']['jobId'])
            self.stop = True


        wait = WebDriverWait(self.driver, 10)
        wait.until(lambda loaded: self.driver.execute_script("return document.readyState;") == "complete")

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
