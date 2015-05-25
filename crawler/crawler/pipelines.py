# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

from crawler.utils import DEBUG, INFO, WARNING, ERROR
from crawler.items import JobsBankItem
from scrapy import log
from scrapy.exceptions import DropItem
from twisted.enterprise import adbapi
from datetime import datetime
from dateutil.parser import parse
from unidecode import unidecode
import traceback
import pdb

class CrawlerPipeline(object):
    def process_item(self, item, spider):
        return item

class FilterFieldsPipeline(object):
    """A pipeline for filtering out items which contain certain words in their
    description"""

    # put all words in lowercase
    fields_to_filter = ['title', 'description', 'requirements']

    def process_item(self, item, spider):
        for field in self.fields_to_filter:
            value = item[field]
            item[field] = ' '.join(value)
        else:
            return item


class RequiredFieldsPipeline(object):
    """A pipeline to ensure the item have the required fields."""

    required_fields = ('jobId', 'title', 'description', 'requirements')

    def process_item(self, item, spider):
        for field in self.required_fields:
            if field not in item:
                raise DropItem("Field '%s' missing: %r" % (field, item))
        return item

class MySQLStorePipeline(object):
    """A pipeline to store the item in a MySQL database.
    This implementation uses Twisted's asynchronous database API.
    """

    def __init__(self, dbpool):
        self.dbpool = dbpool

    @classmethod
    def from_settings(cls, settings):        
        dbargs = dict(
            host=settings['MYSQL_HOST'],
            db=settings['MYSQL_DBNAME'],
            user=settings['MYSQL_USER'],
            passwd=settings['MYSQL_PASSWD'],
            charset='utf8',
            use_unicode=True,
        )
        dbpool = adbapi.ConnectionPool('MySQLdb', **dbargs)
        return cls(dbpool)

    def process_item(self, item, spider):
        # run db query in the thread pool
        d = self.dbpool.runInteraction(self._do_upsert, item, spider)
        d.addErrback(self._handle_error, item, spider)
        # at the end return the item in case of success or failure
        d.addBoth(lambda _: item)
        # return the deferred instead the item. This makes the engine to
        # process next item (according to CONCURRENT_ITEMS setting) after this
        # operation (deferred) has finished.
        return d

    def _do_upsert(self, conn, item, spider):
        """Perform an insert or update."""

        jobId = self._get_id(item)
        now = datetime.utcnow().replace(microsecond=0).isoformat(' ')

        ret = self._check_if_exists(conn, 'job', {'jobId': jobId})

        INFO(ret)

        value_dict = {
                    'jobId': jobId,
                    'title': item['title'], 
                    'description': item['description'], 
                    'requirements': item['requirements'], 
                    'salary': item['salary'],
                    'shiftPattern': item['shiftPattern'],
                    'workingHours': item['workingHours'],
                    'noOfVacancies': int(item['noOfVacancies']),
                    'yearsOfExp': item['yearsOfExp'],
                    'url': item['url'], 
                    'postingDate': parse(item['postingDate']),
                    'closingDate': parse(item['closingDate']),
                    'lastUpdated': now
                }

        if ret:
            self._update(conn, "job", set_pairs=value_dict, where_pairs={'jobId': jobId})
            INFO("Item updated in db: %s" % (jobId))
        else:
            self._insert(conn, "job", value_dict)
            self._insert_categories(conn, item)
            self._insert_emp_type(conn, item)
            self._insert_industry(conn, item)
            self._insert_location(conn, item)

            INFO("Item stored in db: %s" % (jobId))

    def _handle_error(self, failure, item, spider):
        """Handle occurred on db interaction."""
        # do nothing, just log
        failure.printTraceback()
        ERROR("FAILURE!!!")

    def _get_id(self, item):
        """Generates an unique identifier for a given item."""
        # hash based solely in the url field
        return item['jobId'].strip()

    def _insert_categories(self, conn, item):
        """
            Inserts all categories for an item if not already exist.
            Also associates the categories to the item
        """
        jobId = self._get_id(item)

        category_id_list = []
        categories = item['categories']

        for category in categories:
            ret = self._check_if_exists(conn, "job_category", {"category": category})
            if ret:
                category_id = self._get_one(conn, "job_category", ["categoryId"], {"category": category})
            else:
                self._insert(conn, "job_category",\
                    {
                        'category': category
                    })
                category_id = conn.lastrowid

            category_id_list.append(category_id)

        for category_id in category_id_list:
            ret = self._check_if_exists(conn, "assoc_job_job_category", {"jobId": jobId, "categoryId": category_id})
            if not ret:
                self._insert(conn, "assoc_job_job_category",\
                    {
                        "jobId": jobId, 
                        "categoryId": category_id
                    })

    def _insert_emp_type(self, conn, item):
        """
            Inserts all categories for an item if not already exist.
            Also associates the categories to the item
        """
        jobId = self._get_id(item)

        emp_type_id_list = []
        empTypes = item['empType']

        for etype in empTypes:
            ret = self._check_if_exists(conn, "employment_type", {"type": etype})
            if ret:
                emp_id = self._get_one(conn, "employment_type", ["empId"], {"type": etype})
            else:
                self._insert(conn, "employment_type",\
                    {
                        'type': etype
                    })
                emp_id = conn.lastrowid

            emp_type_id_list.append(emp_id)

        for emp_id in emp_type_id_list:
            ret = self._check_if_exists(conn, "assoc_job_employment_type", {"jobId": jobId, "empId": emp_id})
            if not ret:
                self._insert(conn, "assoc_job_employment_type",\
                    {
                        "jobId": jobId, 
                        "empId": emp_id
                    })

    def _insert_industry(self, conn, item):
        """
            Inserts all categories for an item if not already exist.
            Also associates the categories to the item
        """
        jobId = self._get_id(item)

        industry_id_list = []
        industry = item['industry']

        ret = self._check_if_exists(conn, "industry", {"description": industry})
        if ret:
            industry_id = self._get_one(conn, "industry", ["industryId"], {"description": industry})
        else:
            self._insert(conn, "industry",\
                {
                    'description': industry
                })
            industry_id = conn.lastrowid


        ret = self._check_if_exists(conn, "assoc_job_industry", {"jobId": jobId, "industryId": industry_id})
        if not ret:
            self._insert(conn, "assoc_job_industry",\
                {
                    "jobId": jobId, 
                    "industryId": industry_id
                })

    def _insert_location(self, conn, item):
        """
            Inserts all categories for an item if not already exist.
            Also associates the categories to the item
        """
        jobId = self._get_id(item)

        location_id_list = []
        location = item['location']

        ret = self._check_if_exists(conn, "location", {"description": location})
        if ret:
            location_id = self._get_one(conn, "location", ["locationId"], {"description": location})
        else:
            self._insert(conn, "location",\
                {
                    'description': location
                })
            location_id = conn.lastrowid


        ret = self._check_if_exists(conn, "assoc_job_location", {"jobId": jobId, "locationId": location_id})
        if not ret:
            self._insert(conn, "assoc_job_location",\
                {
                    "jobId": jobId, 
                    "locationId": location_id
                })



    def _check_if_exists(self, conn, table, where_pairs):
        where = ' AND '.join(["{key}=%s".format(key=k) for (k, v) in where_pairs.iteritems()])
        values = tuple(where_pairs.values())
        stmt = """SELECT EXISTS(SELECT 1 FROM {table} WHERE {where})""".format(table=table, where=where)
        conn.execute(stmt, (values))
        DEBUG(conn._executed)
        ret = conn.fetchone()[0]
        DEBUG("Returned %r" % ret)
        return ret

    def _get_one(self, conn, table, select_fields, where_pairs=None):
        select_fields = ', '.join(select_fields)
        stmt = """SELECT %s from %s""" % (select_fields, table)
        
        if not where_pairs:
            stmt += ' WHERE {where}'
            where = ' AND '.join(["{key}=%s".format(key=k) for (k, v) in where_pairs.iteritems()])
            values = tuple(where_pairs.values())
            conn.execute(stmt.format(where=where), values)
        else:
            conn.execute(stmt)

        ret = conn.fetchone()[0]
        return ret

    def _insert(self, conn, table, field_value_pairs):
        template = ', '.join(['%s'] * len(field_value_pairs))
        fields = ', '.join(field_value_pairs.keys())
        args = tuple(field_value_pairs.values())

        stmt = "INSERT INTO {table} ({fields}) VALUES ({template})".format(table=table, fields=fields, template=template)
        conn.execute(stmt, args)
        DEBUG(conn._executed)

        return conn.lastrowid

    def _update(self, conn, table, set_pairs, where_pairs):
        sset = ', '.join(["{key}=%s".format(key=k) for (k, v) in set_pairs.iteritems()])
        where = ' AND '.join(["{key}=%s".format(key=k) for (k, v) in where_pairs.iteritems()])
        args = tuple(set_pairs.values() + where_pairs.values())

        stmt = "UPDATE {table} SET {sset} WHERE {where}".format(table=table, sset=sset, where=where)
        conn.execute(stmt, args)