import db
import sys
import numpy
import string
from persist import *
from collections import defaultdict
from scipy import sparse
from numpy.linalg import norm


class NearestNeighbors:

  def __init__(self):
    pass

  def index(self, data):
    """ 
      Creates index of books to userid-rating. The average rating for an
      individual user is also calculated for later processing during the
      computation of item-item similarity.  This is to account for the 
      different rating scales users are likely to have.  

      data: tuple of (userid, bookid, rating) obtained from db
    """

    # load indexes of books and users into memory
    booktoindex = load_obj('booktoindex.pkl')
    usertoindex = load_obj('usertoindex.pkl')

    # used to calculate the average user rating
    userratings = defaultdict(lambda: list())
    # main index 
    idx_dict = defaultdict(lambda: dict())

    for rating in data:
      userid = rating[1]
      bookid = rating[2]
      user_rating = rating[3]

      # get book/user index from their id
      bookindex = booktoindex[bookid]
      userindex = usertoindex[userid]

      idx_dict[bookindex][userindex] = user_rating
      userratings[userindex].append(user_rating)

    # turn the index into a list for easier processing when computing item similarities
    idx_list = [idx_dict[i] for i in xrange(len(idx_dict))]
    serialize_obj(idx_list, 'index.pkl')

    # find user average rating
    avgrating = {}
    for index, ratings in userratings.items():
      avg = float(sum(ratings)) / len(ratings)
      avgrating[index] = avg

    serialize_obj(avgrating, 'avgrating.pkl')
    return (idx_list, avgrating)
    #print len(idx_list)


  def sim_matrix(self, index, avgrating):
    """
      Stores a item-item similarity "matrix" to disk.  This matrix is actually
      a dictionary of bookids -> similarbookid, similarity score.  This representation
      of similarities is more space efficient than a matrix due to the sparse nature of the 
      data.

      Adjusted Cosine similarity is used to compute item-item similarities.  This is useful because
      this approach accounts for differences in user rating scales.
    """

    #index = load_obj('index.pkl')
    books = load_obj('indextobook.pkl') 
    bookstoindex = load_obj('booktoindex.pkl')
    usersindex = load_obj('usertoindex.pkl')
    #avgrating = load_obj('avgrating.pkl')

    indexlen = len(index)
    usersetlen = len(usersindex)
    print 'indexlen', indexlen
    print 'books', len(books)
    print 'users', len(usersindex)

    # hold k nearest neighbors.
    knn = defaultdict(lambda: list())

    # compute n(n-1)/2 similarities instead of n^2
    for i in xrange(indexlen):

      for j in xrange(i+1, indexlen):
        intersections_userid = []
        num_iters = 0

        # only calculate similarity if there are enough users who have 
        # co-rated the same books.  Here the threshold is set at 2, but
        # should be increased as the sample size increases. This optimization
        # greatly impacts the efficiency of this loop.
        # Also store userids that are found to satisfy this condition inorder
        # to avoid operations on vectors of enormous size.
        for user in index[i].iterkeys():
          if user in index[j]:
            intersections_userid.append(user)
            num_iters += 1

        if num_iters >= 3:
          vec1 = self.create_vector(index[i], avgrating, intersections_userid) 
          vec2 = self.create_vector(index[j], avgrating, intersections_userid)
          # calculate adjusted cosine sim
          cos_sim = numpy.dot(vec1, vec2) / (norm(vec1) * norm(vec2))

          # similarities are symmetric so store both
          knn[i].append((j,cos_sim, num_iters))
          knn[j].append((i, cos_sim, num_iters))
      print i
    totalbooks = i
    serialize_obj(dict(knn), 'knn_dict.pkl')

    i = 0
    for k,v in knn.items():
      print k,v
      i+=1
    print i
    print len(knn)
    print totalbooks
    return knn


  def create_vector(self, ratings_dict, avgrating, intersection_bookids):
    """
      Creates a vector (list) of size len(intersections). The dimensions are
      the ratings of the users of the co-rated items.  The average rating for
      an indivdual user is subtracted from their associated actual rating (to
      account of differences in user rating tendencies).
    """

    return [ratings_dict[intersect] - float(avgrating[intersect]) for intersect in intersection_bookids]

  def recommend(self, knn):
    """
      Creates and html page displaying recommendations books.  The books that 
      are aligned left (A) are the "given" books while those books underneath 
      A and indented are recommended based on A. This is showing the knn data 
      structure. This can easily be adapted to recommend a book given that a user
      likes another book.
    """

    db_instance = db.DB()
    #knn = load_obj('knn_dict.pkl')
    indextobook = load_obj('indextobook.pkl')

    html = ['<html><body><table>']
    for book1, ratings in knn.items():
      tmp = []
      for book2, sim, iters in ratings:
        # Set a threshold for what are considered "similar enough books". This is highly
        # dependent on the data.
        if sim > 0.20:
          title, desc, author, image, salesrank = db_instance.getbookattrs(indextobook[book2])
          tmp.append('<tr><td width="150px"></td><td><img src="http://ecx.images-amazon.com/images/I/%s" \
                      width="75"><br>Title: %s<br>Description: %s<br>Authors: %s<br>SalesRank: %s<br>Adj \
                      Cosine Sim: %f</td><td>Intersection: %d</td></tr>' % 
                      (image, title, desc, author, salesrank, sim, iters))
      if tmp:
        title, desc, author, image, salesrank = db_instance.getbookattrs(indextobook[book1])
        html.append('<tr><td colspan=2><img src="http://ecx.images-amazon.com/images/I/%s" width="75px"> \
                    <br>Title: %s<br>Desc: %s<br>Authors: %s<br>SalesRank: %s</td></tr>' % 
                    (image, title, desc, author, salesrank))
        html.extend(tmp)
    html.append('</table></body></html>')

    # write html page to disk
    f = open('bookrec.html', 'w')
    f.write('\n'.join(html))
    f.close()

  def test_recommend(self, bookset, knn):
    """
    """

    bookset = load_obj('test_bookset.pkl')
    #db_instance = db.DB()
    #knn = load_obj('knn_dict.pkl')
    indextobook = load_obj('indextobook.pkl')

    html = ['<html><body><table>']
    for book1, ratings in knn.items():
      tmp = []
      for book2, sim, iters in ratings:
        # Set a threshold for what are considered "similar enough books". This is highly
        # dependent on the data.
        if sim > 0.20:
          title, desc, author, image, salesrank = bookset[indextobook[book2]]
          tmp.append('<tr><td width="150px"></td><td><img src="http://ecx.images-amazon.com/images/I/%s" \
                      width="75"><br>Title: %s<br>Description: %s<br>Authors: %s<br>SalesRank: %s<br>Adj \
                      Cosine Sim: %f</td><td>Intersection: %d</td></tr>' % 
                      (image, title, desc, author, salesrank, sim, iters))
      if tmp:
        title, desc, author, image, salesrank = bookset[indextobook[book1]]
        html.append('<tr><td colspan=2><img src="http://ecx.images-amazon.com/images/I/%s" width="75px"> \
                    <br>Title: %s<br>Desc: %s<br>Authors: %s<br>SalesRank: %s</td></tr>' % 
                    (image, title, desc, author, salesrank))
        html.extend(tmp)
    html.append('</table></body></html>')

    # write html page to disk
    f = open('bookrec.html', 'w')
    f.write('\n'.join(html))
    f.close()

def cosine_sim(vec1, vec2):
  """
    Static function used to debug.  Numpy functions are used in actual
    computation for optimization.
  """
  num = sum([vec1[i]*vec2[i] for i in xrange(len(vec1))])
  print num
  result = num / (norm(vec1) * norm(vec2))
  print numpy.dot(vec1, vec2)

  result2 = numpy.dot(vec1, vec2) / (norm(vec1) * norm(vec2))
  return (result, result2)



