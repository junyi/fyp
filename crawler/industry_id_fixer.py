#!/usr/bin/env python

from scrapy.http import TextResponse
from scrapy.selector import Selector

import MySQLdb as mdb
import MySQLdb.cursors as cursors
from contextlib import closing
from scrapy.utils.project import get_project_settings

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait

import pdb

class IndustryIdFixer(object):
    def __init__(self, _id=1):
    	self._id = _id
    	settings = get_project_settings()
        dbargs = dict(
            host=settings['MYSQL_HOST'],
            db=settings['MYSQL_DBNAME'],
            user=settings['MYSQL_USER'],
            passwd=settings['MYSQL_PASSWD'],
            charset='utf8',
            use_unicode=True,
        )
        self.driver = webdriver.PhantomJS(service_args=['--ssl-protocol=any'])
        self.conn = mdb.connect(**dbargs)

    def _check_if_exists(self, table, where_pairs):
        where = ' AND '.join(["{key}=%s".format(key=k) for (k, v) in where_pairs.iteritems()])
        values = tuple(where_pairs.values())
        stmt = """SELECT EXISTS(SELECT 1 FROM {table} WHERE {where})""".format(table=table, where=where)
    	with closing(self.conn.cursor()) as cursor:
	        cursor.execute(stmt, (values))
	        ret = cursor.fetchone()[0]
        return ret

    def _get_one(self, table, select_fields, where_pairs=None):
        select_fields = ', '.join(select_fields)
        stmt = """SELECT %s from %s""" % (select_fields, table)
        
    	with closing(self.conn.cursor()) as cursor:
	        if where_pairs:
	            stmt += ' WHERE {where}'
	            where = ' AND '.join(["{key}=%s".format(key=k) for (k, v) in where_pairs.iteritems()])
	            values = tuple(where_pairs.values())
	            print stmt
	            cursor.execute(stmt.format(where=where), values)
	        else:
	            cursor.execute(stmt)
	        print cursor._executed

        	ret = cursor.fetchone()[0]

        return ret

    def _insert(self, table, field_value_pairs):
        template = ', '.join(['%s'] * len(field_value_pairs))
        fields = ', '.join(field_value_pairs.keys())
        args = tuple(field_value_pairs.values())

        stmt = "INSERT INTO {table} ({fields}) VALUES ({template})".format(table=table, fields=fields, template=template)
    	with closing(self.conn.cursor()) as cursor:
        	cursor.execute(stmt, args)
        	lastrowid = cursor.lastrowid

        return lastrowid

    def get_count(self):
    	stmt = "SELECT COUNT(1) FROM industry"
    	with closing(self.conn.cursor()) as cursor:
            cursor.execute(stmt)
            ret = cursor.fetchone()[0]
            print "Returned %r" % ret
        return ret

    def get_items_with_id(self):
    	stmt = """SELECT j.jobId, j.url, i.industryId AS oldIndustryId, i.description AS oldDesc FROM job j JOIN assoc_job_industry aji 
    			  ON aji.jobId = j.jobId AND aji.industryId = %s
				  JOIN industry i ON aji.industryId = i.industryId """ % self._id

    	with closing(self.conn.cursor(cursors.DictCursor)) as cursor:
            cursor.execute(stmt)
            ret = cursor.fetchall()
        return ret

    def fix_item(self, item):
    	url = item['url']
    	job_id = item['jobId']
    	old_desc = item['oldDesc']
    	old_industry_id = item['oldIndustryId']

    	print "Processing job %s" % job_id

    	try:
    		self.driver.get(url)
        except URLError, e:
            ERROR("Connection error for job %s" % job_id)

        wait = WebDriverWait(self.driver, 10)
        wait.until(lambda loaded: self.driver.execute_script("return document.readyState;") == "complete")

        new_response = TextResponse(url=url, body=self.driver.page_source, encoding='utf-8')

        sel = Selector(new_response)

        industry = sel.xpath("//div[@class='jd_contentRight']/dl[2]//span/text()").extract()[0].strip()
        print "Correct industry found to be: %s" % industry
        ret = self._check_if_exists("industry", {"description": industry})
        if ret:
            new_industry_id = self._get_one("industry", ["industryId"], {"description": industry})
        else:
        	new_industry_id = self._insert("industry",\
                {
                    'description': industry
                })

        stmt = """UPDATE assoc_job_industry
        		  SET industryId = %s
        		  WHERE jobId = %s AND
        		  		industryId = %s0
        		"""

    	with closing(self.conn.cursor(cursors.DictCursor)) as cursor:
        	cursor.execute(stmt, (new_industry_id, job_id, old_industry_id))
        	print "Fixed new industryId to be %d" % new_industry_id




if __name__ == '__main__':
	fixer = IndustryIdFixer()
	print "Found %d items with id=%d" % (fixer.get_count(), fixer._id)
	items = fixer.get_items_with_id()
	for item in items:
		fixer.fix_item(item)
