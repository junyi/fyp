from crawler.utils import DEBUG, INFO, WARNING, ERROR
from scrapy.exceptions import IgnoreRequest
from contextlib import closing
import MySQLdb as mdb
import pdb

class DbFilterMiddleware(object):
    def __init__(self, conn):
        self.conn = conn

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
        conn = mdb.connect(**dbargs)
        return cls(conn)

    def _check_if_exists(self, table, where_pairs):
        where = ' AND '.join(["{key}=%s".format(key=k) for (k, v) in where_pairs.iteritems()])
        values = tuple(where_pairs.values())
        stmt = """SELECT EXISTS(SELECT 1 FROM {table} WHERE {where})""".format(table=table, where=where)
        with closing(self.conn.cursor()) as cursor:
            cursor.execute(stmt, (values))
            DEBUG(cursor._executed)
            ret = cursor.fetchone()[0]
            DEBUG("Returned %r" % ret)
        return ret

    def process_request(self, request, spider):
        
        if 'item' in request.meta:
            job_id = request.meta['item']['jobId']

            if hasattr(spider, 'stop') and spider.stop:
                raise IgnoreRequest("Stopped: Ignoring job %s" % job_id)

            ret = self._check_if_exists('job', {'jobId': job_id})

            if ret:
                INFO("Job %s already exists" % job_id)
                raise IgnoreRequest("Job %s already exists" % job_id)

    # def process_response(request, response, spider):
        