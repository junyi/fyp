# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

from scrapy import Item, Field


class JobsBankItem(Item):
    # define the fields for your item here like:
    jobId = Field()
    title = Field()
    description = Field()
    requirements = Field()
    location = Field()
    industry = Field()
    categories = Field()
    empType = Field()
    workingHours = Field()
    shiftPattern = Field()
    salary = Field()
    jobLevel = Field()
    yearsOfExp = Field()
    postingDate = Field()
    closingDate = Field()
    noOfVacancies = Field()
    url = Field()
