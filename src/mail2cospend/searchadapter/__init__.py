from .rewe import ReweSearchAdapter
from .picnic import PicnicSearchAdapter
from .netto import NettoSearchAdapter
from .searchadapter import SearchAdapter

all_search_adapters = SearchAdapter.__subclasses__()