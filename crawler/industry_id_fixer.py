import MySQLdb as mdb
from contextlib import closing
from scrapy.conf import settings

class IndustryIdFixer(object):
    def __init__(self, id=1):
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

if __name__ == '__main__':
	fixer = IndustryIdFixer()
	print fixer.get_count()