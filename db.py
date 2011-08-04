import string
import MySQLdb as mysqldb
from persist import *
try:
  from config import *
except:
  pass

class DB:
  """
    All book information was obtained from Amazon. A lot of the data was "dirty" and not
    properly cleansed.
  """

  def __init__(self):
    # create both local and remote (DB server)
    self.remote_conn = mysqldb.connect(host=REMOTE_HOST, user=REMOTE_USER, passwd=REMOTE_PASSWD, db=REMOTE_DB)
    self.local_conn = mysqldb.connect(host=HOST, user=USER, passwd=PASSWD, db=LOCAL_DB)

  def get_remote_books(self):
    """ Get all books from remote db server. """

    c = self.remote_conn.cursor()
    c.execute(""" select id, title, description, authors, image_code, sales_rank, rating, 
               stat_reviews from books where title is not null; """)
    result = c.fetchall()
    c.close()

    return result

  def sample_users(self):
    """ 
      Get a sample of users to test the recommender system on. Users that 
      rated around 20 books were chosen. 
    """
    c = self.remote_conn.cursor()
    c.execute(""" select customer_id, count(customer_id) as c from reviews group by customer_id order by c desc limit 4000, 
               5000 """)
    result = c.fetchall()
    c.close()
    return result

  def insert_sample_users(self, userids):
    """ Take sample from remote server and insert into local mysql instance """

    c = self.local_conn.cursor()
    i = 0
    for userid in userids:
    	c.execute(""" insert into sampleid values (%d, '%s') """ % (i, userid[0]))
    	i += 1
    c.close()

  def get_remote_ratings(self):
    """ 
      Get all book ratings from remote db.  Make sure that the book
      did not have a rating of 0 (not sure why these were here in the
      first place) and that the book was somewhat popular (eg. salesrank < 10000).
    """
      
    c = self.remote_conn.cursor()
    c.execute(""" select id, book_id, user_id, customer_id, 
                  rating from reviews where rating > 0 and book_id in \
                  (select id from books where sales_rank < 10000); """)
    #c.execute(""" select id, book_id, user_id, customer_id, 
    #         rating from reviews where rating > 0 and book_id in \
    #         (select id from books where sales_rank < 30000) order by rand() limit 10000;""")
    #print 'row count %d' % c.rowcount
    result = c.fetchall()
    c.close()
    return result

  def insert_ratings(self, items):
    """ Store ratings on local db instance """

    c = self.local_conn.cursor()
    for item in items:
      #if bookid is not null
      item2or3 = item[2] if item[2] else item[3]
      c.execute("insert into ratings values(%d, '%s', %d, %d)" % (item[0], 
                 item2or3, item[1], item[4]))
    c.close()

  def insert_books(self, items):
    """ Grab books from dev server and put on local """

    c = self.local_conn.cursor()
    i=0
    errors = []
    for item in items:
      # quick hack to handle titles/descriptions with double quotes in them.
      # (screws with python string formating).
      item1 = string.replace(item[1], '"', '\\"') if item[1] else ''
      item2 = string.replace(item[2], '"', '\\"') if item[2] else ''
      item3 = string.replace(item[3], '"', '\\"') if item[3] else ''

      #if item[1]: item1 = string.replace(item[1], '"', '\\"')
      #else: item1 = ''

      #if item[2]: item2 = string.replace(item[2], '"', '\\"')
      #else: item2 = ''

      #if item[3]: item3 = string.replace(item[3], '"', '\\"')
      #else: item3 = ''
      try:
        c.execute(""" insert into books values(%d, "%s", "%s", "%s", "%s", %d, %d, %d) """ % 
                 (item[0], item1, item2, item3, item[4], item[5], item[6], item[7]))
      except:
        errors.append(str(item[0]))

    print ' '.join(errors)
    c.close()

  def get_ratings(self):
    """ Get ratings from local db. Used when indexing. """

    c = self.local_conn.cursor()
    c.execute(""" select id, userid, bookid, rating from ratings; """)
    #return c.fetchmany(10)
    results =  c.fetchall()
    # used for testing
    serialize_obj(results, 'test_ratings.pkl')
    return results

  def get_test_books(self):
    """ Get sample set of books for testing """

    c = self.local_conn.cursor()
    c.execute(""" select * from books where id in (select distinct bookid from ratings); """)
    results =  c.fetchall()
    # used for testing
    bookset = {}
    for id, title, desc, authors, image, salesrank, _ , _ in results:
    	bookset[id] = (title, desc, authors, image, salesrank)

    serialize_obj(bookset, 'test_bookset.pkl')

  def userset(self):
    """ 
      Unique users are found. Indexes of userid -> index number
      and index numer -> userid are created. This is useful for
      created the ratings index of bookids -> (userid -> rating).
    """

    c = self.local_conn.cursor()
    c.execute(""" select distinct userid from ratings """)
    result = c.fetchall()

    users = [user[0] for user in result]
    # create index numbers starting from 0
    indextouser = list(enumerate(users))
    serialize_obj(dict(indextouser), 'indextouser.pkl')
    usertoindex = dict([(b,a) for a,b in indextouser])
    serialize_obj(usertoindex, 'usertoindex.pkl')
    print len(usertoindex)

  def itemset(self):
    """ Find unique bookids """

    c = self.local_conn.cursor()
    c.execute(""" select distinct bookid from ratings; """)
    result = c.fetchall()
    c.close()

    items = [item[0] for item in result]
    items.sort()
    indextobook = list(enumerate(items))
    serialize_obj(dict(indextobook), 'indextobook.pkl')
    booktoindex = dict([(b,a) for a,b in indextobook])
    serialize_obj(booktoindex, 'booktoindex.pkl')

  def getbookattrs(self, bookid):
    c = self.local_conn.cursor()
    c.execute(""" select title, description, authors, image, salesrank from books where books.id=%d; """ % bookid)
    attrs = c.fetchone()
    c.close()
    return attrs

  def get_titles(self):
    c = self.local_conn.cursor()
    c.execute(""" select title from books where books.id in (select distinct bookid from ratings); """)
    titles = c.fetchall()
    c.close()
    return titles

  def delete_title(self, bookid):
    c = self.local_conn.cursor()
    c.execute("delete from ratings where bookid = %d" % bookid)
    self.local_conn.commit()
