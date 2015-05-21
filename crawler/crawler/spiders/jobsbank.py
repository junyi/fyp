from crawler.items import JobsBankItem
from scrapy import FormRequest, log, Request
from scrapy.selector import Selector
from scrapy.spider import Spider
from scrapy.http import TextResponse 
from html2text import html2text
from selenium import webdriver
import pdb
import nltk

class JobsBankSpider(Spider):
    name = "jobsbank"
    allowed_domains = ["www.jobsbank.gov.sg"]
    start_urls = []
    current_page = 1

    def __init__(self):
        self.driver = webdriver.Firefox()

    def start_requests(self):
        return [
            FormRequest("https://www.jobsbank.gov.sg/ICMSPortal/portlets/JobBankHandler/SearchResult.do",
                        formdata={
                            '{actionForm.currentPageNumber}': '1',
                            '{actionForm.checkValidRequest}': 'YES',
                            '{actionForm.recordsPerPage}': '100'},  # Multiply by 5 to get the actual no of records
                        method="POST",
                        callback=self.parse_page)]

    def parse_page(self, response):
        sel = Selector(response)
        total_no_of_pages = sel.xpath("//div[@class='page-navigation']//td[7]/text()").extract()[0]
        total_no_of_pages = int(total_no_of_pages)
        log.msg(total_no_of_pages)

        jobs = sel.xpath("//article")

        for job in jobs:
            item = JobsBankItem()
            location = job.xpath(
                ".//td[@class='location']/label/text()").extract()[0]
            title = job.xpath(
                ".//td[@class='jobDesActive']/a[@class='text']/text()").extract()[0]

            item["jobId"] = title[title.index("ID:") + 3: title.rfind(")")]
            log.msg(item["jobId"])
            item["location"] = location

            job_detail_link = sel.xpath(
                ".//td[@class='jobDesActive']/a/@href").extract()[0]
            request = Request(
                "https://www.jobsbank.gov.sg" + job_detail_link, callback=self.parse_job)
            request.meta['item'] = item
            yield request

        if self.current_page < total_no_of_pages:
            log.msg("Done scraping page %d/%d" %
                    (self.current_page, total_no_of_pages))
            self.current_page += 1
            yield FormRequest("https://www.jobsbank.gov.sg/ICMSPortal/portlets/JobBankHandler/SearchResult.do",
                               formdata={
                                   '{actionForm.currentPageNumber}': str(self.current_page),
                                   '{actionForm.checkValidRequest}': 'YES',
                                   '{actionForm.recordsPerPage}': '100'},  # Multiply by 5 to get the actual no of records
                               method="POST",
                               callback=self.parse_page)
        else:
            log.msg("Finished scraping")
            return

    def parse_job(self, response):
        self.driver.get(response.url)

        response = TextResponse(url=response.url, body=self.driver.page_source, encoding='utf-8')
        self.driver.close()
        sel = Selector(response)
        # item = response.meta['item']
        # with open("response.txt", "w") as f:
        #     f.write(response.body_as_unicode())

        item = JobsBankItem()

        item["title"] = sel.xpath("//div[@class='jobDes']//h3/text()").extract()[0].strip()
        
        postingDate = sel.xpath("//div[@class='jobDes']//div/p/text()").extract()[0]
        item["postingDate"] = postingDate[postingDate.index(":") + 1:].strip()

        closingDate = sel.xpath("//div[@class='jobDes']//div/p/text()").extract()[1]
        item["closingDate"] = closingDate[closingDate.index(":") + 1:].strip()

        description = sel.xpath("//div[@id='divMainJobDescription']").extract()
        item["description"] = ''.join([html2text(i) for i in description])

        item["requirements"] = sel.xpath("//div[@id='divMainSkillsRequired']/p/text()").extract()[0].strip()

        item["categories"] = sel.xpath("//div[@class='jd_contentRight']/dl[1]//li/span/text()").extract()

        item["industry"] = sel.xpath("//div[@class='jd_contentRight']/dl[2]//span/text()").extract()[0].strip()

        item["empType"] = sel.xpath("//div[@class='jd_contentRight']/ul[1]//li/span/text()").extract()

        item["workingHours"] = sel.xpath("//div[@class='jd_contentRight']/ul[2]//li/span/text()").extract()[0].strip()

        item["shiftPattern"] = sel.xpath("//div[@class='jd_contentRight']/ul[3]//li/span/text()").extract()[0].strip()

        item["salary"] = sel.xpath("//div[@class='jd_contentRight']/ul[4]//span/text()").extract()[0].strip()

        item["jobLevel"] = sel.xpath("//div[@class='jd_contentRight']/ul[5]//span/text()").extract()[0].strip()

        item["yearsOfExp"] = sel.xpath("//div[@class='jd_contentRight']/ul[6]//li/text()").extract()[0].strip()

        item["noOfVacancies"] = sel.xpath("//div[@class='jd_contentRight']/span[@class='text'][1]/text()").extract()[0].strip()

        yield item
