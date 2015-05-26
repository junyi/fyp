import MySQLdb as mdb
from contextlib import closing
from scrapy.utils.project import get_project_settings

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
        self.conn = mdb.connect(**dbargs)

    def get_count(self):
    	stmt = "SELECT COUNT(1) FROM industry"
    	with closing(self.conn.cursor()) as cursor:
            cursor.execute(stmt)
            print cursor._executed
            ret = cursor.fetchone()[0]
            print "Returned %r" % ret
        return ret

    def get_items_with_id(self):
    	stmt = """SELECT j.* FROM job j, industry i, assoc_job_industry aji 
    			  WHERE aji.jobId = j.jobId AND
    					aji.industryId = %s """ % self._id

    	with closing(self.conn.cursor()) as cursor:
            cursor.execute(stmt)
            print cursor._executed
            ret = cursor.fetchall()
            print "Returned %r" % ret
        return ret


if __name__ == '__main__':
	fixer = IndustryIdFixer()
	print "Found %d items with id=%d" % (fixer.get_count(), fixer._id)
	print fixer.get_items_with_id()
