# -*- coding: utf-8 -*-

# Scrapy settings for crawler project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#

BOT_NAME = 'crawler'

SPIDER_MODULES = ['crawler.spiders']
NEWSPIDER_MODULE = 'crawler.spiders'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
USER_AGENT = 'Googlebot/2.1 (+http://www.googlebot.com/bot.html)'

# DEPTH_PRIORITY = 1
# SCHEDULER_DISK_QUEUE = 'scrapy.squeue.PickleFifoDiskQueue'
# SCHEDULER_MEMORY_QUEUE = 'scrapy.squeue.FifoMemoryQueue'

DUPEFILTER_DEBUG = True
LOG_LEVEL = "DEBUG"
LOG_FILE = "out.log"

ITEM_PIPELINES = {
    'crawler.pipelines.MySQLStorePipeline': 800,
    'crawler.pipelines.FilterFieldsPipeline': 900,
    'crawler.pipelines.RequiredFieldsPipeline': 1000
}

# MYSQL_HOST = 'localhost'
# MYSQL_DBNAME = 'jobsbank'
# MYSQL_USER = 'crawler'
# MYSQL_PASSWD = 'heejunyifypcrawler'

MYSQL_HOST = 'localhost'
MYSQL_DBNAME = 'jobsbank'
MYSQL_USER = 'root'
MYSQL_PASSWD = ''