import nearestn
import db

def main():
  nn = nearestn.NearestNeighbors()
  db_instance = db.DB()
  db_instance.userset()
  db_instance.itemset()
  ratings = db_instance.get_ratings()
  nn.index(ratings)
  nn.sim_matrix()
  nn.recommend(None)

if __name__ == '__main__':
	main()
