from ponzu.artemis.artemis import Artemis


def test_artemis_chains():
  # -- initialize object 
  artemis = Artemis()
  # -- get chain metrics
  df = artemis.getChainMetrics()
  assert len(df) > 0

def test_artemis_categories():
  # -- initialize object 
  artemis = Artemis()
  # -- get chain activity by category
  df = artemis.getChainActivityByCategory()
  assert len(df) > 0

def test_artemis_apps():
  # -- initialize object 
  artemis = Artemis()
  # -- get chain activity by app
  df = artemis.getChainActivityByApp()
  assert len(df) > 0