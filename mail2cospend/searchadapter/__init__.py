import logging
from .rewe import ReweSearchAdapter
from .picnic import PicnicSearchAdapter
from .netto import NettoSearchAdapter
from .searchadapter import SearchAdapter

all_search_adapters = SearchAdapter.__subclasses__()

logging.debug(f"Loaded search adapters: {", ".join(adapter.adapter_name() for adapter in all_search_adapters)}")
