"""Root-sum-square propagation of independent relative uncertainties
(GUM, JCGM 100:2008, eq. 10, for products/quotients)."""
import numpy as np
def rss(*rel):  return float(np.sqrt(np.sum(np.square(rel))))
