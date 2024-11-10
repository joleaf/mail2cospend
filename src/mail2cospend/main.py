import logging
from threading import Event

from mail2cospend.cospendconnector import publish_bongs

from mail2cospend.config import load_config
from mail2cospend.mailconnector import get_imap_connection
from mail2cospend.searchadapter import all_search_adapters

exit_event = Event()


def run(dry=False):
    config = load_config()
    logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p',
                        level=config.loglevel)

    logging.debug(f"Loaded search adapters: ")
    for adapter in all_search_adapters:
        logging.debug(f"  - {adapter.adapter_name()}")

    while not exit_event.is_set():
        imap = get_imap_connection(config)

        bons = list()
        for Adapter_cls in all_search_adapters:
            adapter = Adapter_cls(config, imap)
            this_bons = adapter.search()
            bons += this_bons
            imap.close()
        imap.shutdown()

        if dry:
            logging.info("Dry run. Results:")
            for bon in bons:
                logging.info(bon)
            break
        else:
            publish_bongs(bons, config)

        logging.info(f"Waiting {config.interval} seconds before next run")
        exit_event.wait(config.interval)
