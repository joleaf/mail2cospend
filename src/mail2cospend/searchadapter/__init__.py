from .netto import NettoSearchAdapter
from .picnic import PicnicSearchAdapter
from .planted import PlantedSearchAdapter
from .rewe import ReweSearchAdapter
from .edeka import EdekaSearchAdapter
from .ikea import IkeaSearchAdapter
from .searchadapter import SearchAdapter

all_search_adapters = SearchAdapter.__subclasses__()

__all__ = [cls.__name__ for cls in all_search_adapters] + ['SearchAdapter']
