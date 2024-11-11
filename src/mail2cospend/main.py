import logging
from threading import Event

from mail2cospend.cospendconnector import publish_bongs, test_connection

from mail2cospend.config import load_config
from mail2cospend.mailconnector import get_imap_connection
from mail2cospend.searchadapter import all_search_adapters

exit_event = Event()


def run(dry=False):
    config = load_config(exit_event)
    logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p',
                        level=config.loglevel)
    if not test_connection(config):
        exit(1)
    logging.debug(f"Loaded search adapters: ")
    for adapter in all_search_adapters:
        logging.debug(f"  - {adapter.adapter_name()}")

    while not exit_event.is_set():
        imap = get_imap_connection(config)
        if imap is None or exit_event.is_set():
            exit(1)

        bons = list()
        for Adapter_cls in all_search_adapters:
            adapter = Adapter_cls(config, imap)
            this_bons = adapter.search()
            bons += this_bons
            imap.close()
        imap.shutdown()

        if exit_event.is_set():
            exit(1)

        if dry:
            logging.info("Dry run. Results:")
            for bon in bons:
                logging.info(bon)
            break
        else:
            publish_bongs(bons, config)
        if exit_event.is_set():
            exit(1)
        logging.info(f"Waiting {config.interval} seconds before next run")
        exit_event.wait(config.interval)
