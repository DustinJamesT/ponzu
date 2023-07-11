


# -- local imports
from ._api import getAppSummaryTable


def stringifyList(chains): 
  # -- make chains a str and remove brackets and spaces and quotes
  chains = str(chains).replace('[', '').replace(']', '').replace(' ', '').replace("'", "")

  return chains


def getCategoryMap():
  apps = getAppSummaryTable()

  # -- create dictionary of value ad parentValue columns 
  category_map = dict(zip(apps['label'], apps['parentValue']))

  return category_map