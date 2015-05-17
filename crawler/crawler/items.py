# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class JobItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    title = scrapy.Field()
    location = scrapy.Field()
    industry = scrapy.Field()
    categories = scrapy.Field()
    empType = scrapy.Field()
    description = scrapy.Field()
    yearsOfExp = scrapy.Field()
    postingDate = scrapy.Field()
    closingDate = scrapy.Field()
    requirements = scrapy.Field()

