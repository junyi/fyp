from scrapy import log

def DEBUG(msg):
    return log.msg(msg, level=log.DEBUG)

def INFO(msg):
    return log.msg(msg, level=log.INFO)

def WARNING(msg):
    return log.msg(msg, level=log.WARNING)

def ERROR(msg):
    return log.msg(msg, level=log.ERROR)