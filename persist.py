import cPickle as pickle

def serialize_obj(obj, filename):
  """ Writes obj (in this case a dict) to disk """

  f = open(filename, 'wb')
  pickle.dump(obj, f)
  f.close()

def load_obj(filename):
  data = open(filename, 'rb')
  obj = pickle.load(data)
  data.close()
  return obj
