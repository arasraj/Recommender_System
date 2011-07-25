import db
import re
import Levenshtein as levens
from fuzzywuzzy import fuzz

class Cleanser():
  """ 
    The dataset had numerous alternative versions books that were
    not necessary.  This class contains functions to find and delete such
    books.  SeatGeek's fuzzy string matching library was initially used but 
    found to be too computationly slow for this dataset.  As a result Google's
    Levenshtein library was used because it's python module is implemented in C.
    
    Finding the correct value of the threshold of whether two titles are similar was
    somewhat difficult.  If the value is set to high the algorithm misses some books 
    that are indeed the same but with slightly different titles.  Threshold values
    that are two low will consider books titles the same when they are not.  The appropriate
    value I found to produce the best results was 0.887.
  """
    

  def __init__(self):
    db_instance = db.DB()

  def process_titles(self):
    titles = db_instance.get_tiles()

    # Book titles often contained non-essential information such as the binding and edition.
    # This was usually between parens.  As a result, all information between parens was 
    # discarded.
    # Levenshtien.set_ratio() expects a list as an argument
    titles = [(re.sub(r'\(.+\)', '', title[0]).strip().split(), title[0]) for title in titles]
    return titles


  def print_dups(self, bookids):

    for bookid1, bookid2, booktitle1, booktitle2 in bookids:
    	print booktitle1
    	print booktitle2
    	print ''

    print 'Len dups:', len(bookids)

  def delete_dups(self, dups):
    c = self.local_conn.cursor()
    
    # When two books are found with the same title, the one with the longer
    # title is deleted. This is because the longer title usually contains 
    # the non-essential information.
    for bookid1, bookid2, booktitle1, booktitle2 in dups:
    	largest_title = bookid1 if len(booktitle1) > len(booktitle2) else bookid2
    	db_instance.delete_title(largest_title)


  def finddups(self, titles):
    """
      Finds title duplicates using approximate string matching techniques.
    """

    print 'Len titles:', len(titles)
    indextobook = self.load('indextobook.pkl')

    total = 0
    dups = []
    for i in xrange(len(titles)):
      ititle = titles[i][0]
      orig_title = titles[i][1]
      for j in xrange(i+1, len(titles)):
        #sim = fuzz.token_sort_ratio(titles[i][0], titles[j][0])
        ratio = levens.setratio(ititle, titles[j][0])
        if ratio > 0.887:
          print indextobook[i], indextobook[j]
          dups.append((indextobook[i], indextobook[j], orig_title, titles[j][1]))
          total += 1
      print i

    print 'Total dups:', total
    return dups

  def process(self):
    titles = self.gettitles()
    bookids = self.finddups(titles)
    #self.deletedups(bookids) 
    self.printdups(bookids)


