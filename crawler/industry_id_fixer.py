import MySQLdb as mdb

class IndustryIdFixer(object):
    def __init__(self, conn, id=1):
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

    def get_count(self):
    	stmt = "SELECT COUNT(1) FROM industry"
    	with closing(self.conn.cursor()) as cursor:
            cursor.execute(stmt, (values))
            DEBUG(cursor._executed)
            ret = cursor.fetchone()[0]
            DEBUG("Returned %r" % ret)
        return ret

if __name__ == '__main__':
	fixer = IndustryIdFixer()
	print fixer.get_count()