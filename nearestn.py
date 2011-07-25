import string
import numpy
import sys

from persist import *
from collections import defaultdict
from scipy import sparse
from numpy.linalg import norm


class NearestNeighbors:

  def __init__(self, data):
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
    #print len(idx_list)


  def sim_matrix(self):
    """
      Stores a item-item similarity "matrix" to disk.  This matrix is actually
      a dictionary of bookids -> similarbookid, similarity score.  This representation
      of similarities is more space efficient than a matrix due to the sparse nature of the 
      data.

      Adjusted Cosine similarity is used to compute item-item similarities.  This is useful because
      this approach accounts for differences in user rating scales.
    """

    index = load_obj('index.pkl')
    books = load_obj('indextobook.pkl') 
    bookstoindex = load_obj('booktoindex.pkl')
    usersindex = load_obj('usertoindex.pkl')
    avgrating = load_obj('avgrating.pkl')

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
        intersection_userid = []
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

        if num_iters >= 2:
          vec1 = self.create_vector(index[i], avgrating, intersections_userid) 
          vec2 = self.create_vector(index[j], avgrating, intersections_userid)
          # calculate adjusted cosine sim
          cos_sim = numpy.dot(vec1, vec2) / (norm(vec1) * norm(vec2))

          # similarities are symmetric so store both
          knn[i].append((j,cos_sim, iters))
          knn[j].append(i, cos_sim, iters))
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


  def create_vector(self, ratings_dict, avgrating, intersection_bookids):
    """
      Creates a vector (list) of size len(intersections). The dimensions are
      the ratings of the users of the co-rated items.  The average rating for
      an indivdual user is subtracted from their associated actual rating (to
      account of differences in user rating tendencies).
    """

    return [ratings_dict[intersect] - avgrating[intersect]for intersect in intersection_bookids]


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



