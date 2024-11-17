import logging
from threading import Event

from mail2cospend.config import load_config, Config
from mail2cospend.cospendconnector import publish_bongs, test_connection, get_cospend_project_infos
from mail2cospend.mailconnector import get_imap_connection
from mail2cospend.searchadapter import all_search_adapters

exit_event = Event()


def _init() -> Config:
    config = load_config(exit_event)

    if not test_connection(config):
        exit(1)
    return config


def run(dry=False):
    config = _init()
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


def print_cospend_project_infos():
    config = _init()
    project_infos = get_cospend_project_infos(config)
    logging.info("Categories  (Used for  COSPEND_CATEGORYID_... )")
    logging.info("----------")
    for val in project_infos.categories:
        logging.info(f"  - {val}")
    logging.info("")
    logging.info("Payment Modes  (Used for  COSPEND_PAYMENTMODEID_... )")
    logging.info("-------------")
    for val in project_infos.paymentmodes:
        logging.info(f"  - {val}")
    logging.info("")
    logging.info("Members  (Used for  COSPEND_PAYED_FOR_...  (multiple seperated by a ',') and  COSPEND_PAYER_... )")
    logging.info("-------")
    for val in project_infos.members:
        logging.info(f"  - {val}")
