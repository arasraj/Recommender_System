import MySQLdb as mysqldb
from config import *
from collections import defaultdict
import cPickle as pickle
import string
from scipy import sparse
import numpy

class Ratings:

  def __init__(self):
    self.remote_conn = mysqldb.connect(host=REMOTE_HOST, user=REMOTE_USER, passwd=REMOTE_PASSWD, db=REMOTE_DB)
    self.local_conn = mysqldb.connect(host=HOST, user=USER, passwd=PASSWD, db=DB)

  def extract_book_attrs(self):
    c = self.remote_conn.cursor()
    c.execute("select id, title, description, authors, sales_rank, rating from books")
    result = c.fetchall()
    c.close()

    # pickle books data
    #fout = open('books.pkl', 'wb')
    #pickle.dump(result, fout)
    #fout.close()
    return result

  def extract_ratings(self):
    c = self.remote_conn.cursor()
    c.execute("""select id, book_id, user_id, customer_id, rating from reviews where rating is not NULL;""")
    result = c.fetchall()
    print 'row count %d' % c.rowcount
    c.close()
    return result

  def transfer_ratings(self, items):
    c = self.local_conn.cursor()
    for item in items:
      #if bookid is not null
      if item[2]:
        c.execute("insert into ratings values(%d, '%s', %d, %d)" % (item[0], item[2], item[1], item[4]))
      elif item[3]:
        c.execute("insert into ratings values(%d, '%s', %d, %d)" % (item[0], item[3], item[1], item[4]))
    c.close()

  def transfer_books(self, items):
    """ grab books from dev server and put on local """
    """ from pickled data """
    c = self.local_conn.cursor()
    items = self.load('books.pkl')
    i=0
    errors = []
    for item in items:
      if item[1]: item1 = string.replace(item[1], '"', '\\"')
      else: item1 = ''

      if item[2]: item2 = string.replace(item[2], '"', '\\"')
      else: item2 = ''

      if item[3]: item3 = string.replace(item[3], '"', '\\"')
      else: item3 = ''
      try:
        c.execute("""insert into books values(%d, "%s", "%s", "%s", %d, %d)""" % 
                (item[0], item1, item2, item3, item[4], item[5]))
      except:
        errors.append(str(item[0]))
      i+=1
      print i
    ' '.join(errors)
    c.close()

  def get_ratings(self):
    """ Get ratings from local db """

    c = self.local_conn.cursor()
    c.execute("select * from ratings;")
    return c.fetchall()

  def unique_items(self, table, field, pkl_filename):
    c = self.local_conn.cursor()
    c.execute(""" select %s from %s; """ % (field, table))
    result = c.fetchall()
    c.close()
    items = set([item[0] for item in result])
    #books = list(enumerate(books))
    print len(items)
    self.serialize(items, pkl_filename) 
    #print books

  def serialize(self, obj, filename):
    """ Writes obj (in this case a dict) to disk """

    f = open(filename, 'wb')
    pickle.dump(obj, f)
    f.close()

  def load(self, filename):
    data = open(filename, 'rb')
    idx_dict = pickle.load(data)
    data.close()
    print len(idx_dict)
    #for key,value in idx_dict.items():
    #	print key, value

class Indexer:
  def __init__(self, data):
    self.data = data

  def index(self):
    """ Creates index of user with rating/bookid """
    idx_dict = defaultdict(lambda: dict())
    for rating in self.data:
    	userid = rating[1]
    	user_rating = rating[3]
    	bookid = rating[2]

    	idx_dict[userid][bookid] = user_rating
    #print idx_dict
    self.serialize(dict(idx_dict), 'index.pkl')

  def rated_bookset(self):
    ratings = self.load('index.pkl')
    bookset = set()
    i=0
    for books in ratings.values():
      for book in books.keys():
      	bookset.add(book)
      i+=1
      print i

    self.serialize(bookset, 'rated_bookset.pkl')
    #print bookset
    #print len(bookset)


  def useritem_matrix(self):
    books = self.load('rated_bookset.pkl')
    ratings = self.load('index.pkl')

    users = ratings.keys()
    users.sort() #???
    m = sparse.lil_matrix((len(ratings), len(books)))
    #m = numpy.zeros((len(ratings), len(books)))
    #m = []
    enumbooks = list(enumerate(books))
    books_dict = dict([(b,a) for a,b in enumbooks])
    i=0
    for userindex, user in enumerate(users):
      for book in ratings[user].keys():
        #print 'book: ', book
        #print 'user: ', user
        #print 'book idx: ', books_dict[book]
        #print 'rating: ', ratings[user].get(book,0)
        m[userindex, books_dict[book]] = ratings[user].get(book, 0)
      i+=1
      print i
    self.serialize(m, 'useritem_mtrx.pkl')
    return m

  def sim_matrix(self):
    m = self.load('useritem_mtrx.pkl')
    m2 = m.tocsr()
    len_col = m2.get_shape()[1]
    print len_col
    for i in xrange(len_col):
      for j in xrange(i+1, len_col):
      	m2.getrow(j)
      	print j
      print i

  def serialize(self, obj, filename):
    """ Writes obj (in this case a dict) to disk """

    f = open(filename, 'wb')
    pickle.dump(obj, f)
    f.close()

  def load(self, filename):
    data = open(filename, 'rb')
    idx_dict = pickle.load(data)
    data.close()
    #print len(idx_dict)
    return idx_dict
    #for key,value in idx_dict.items():
    #	print key, value

if __name__ == '__main__':
	ratings = Ratings()
	#ratings.unique_items('ratings', 'userid', 'useridset.pkl')
	##result = ratings.extract_ratings()
	#result = ratings.extract_book_attrs()
	#ratings.transfer_books(result)
	##ratings.transfer_ratings(result)
	#user_ratings = ratings.get_ratings()
	indexer = Indexer(None)
	#indexer.useritem_matrix()
	indexer.sim_matrix()
	#indexer.rated_bookset()
	#indexer.index()
	#indexer.load('index.pkl')
    
    
