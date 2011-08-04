import nearestn
import db
import sys 
from persist import *

def main():
  nn = nearestn.NearestNeighbors()
  db_instance = db.DB()
  db_instance.userset()
  db_instance.itemset()
  ratings = db_instance.get_ratings()
  nn.index(ratings)
  nn.sim_matrix()
  nn.recommend(None)

def test():
  nn = nearestn.NearestNeighbors()
  bookset = load_obj('test_bookset.pkl')
  ratings = load_obj('test_ratings.pkl')
  index, avgrating = nn.index(ratings)
  knn = nn.sim_matrix(index, avgrating)
  nn.test_recommend(bookset, knn)

if __name__ == '__main__':

  try:
    dotest = sys.argv[1]
  except:
    dotest = None

  if dotest: test()
  else: main()
