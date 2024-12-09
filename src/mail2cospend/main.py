import logging
from threading import Event

import click

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
    logging.debug("Enabled adapters:")
    for adapter in all_search_adapters:
        if config.is_adapter_enabled(adapter.adapter_name()):
            logging.debug(f"  - {adapter.adapter_name()}")

    while not exit_event.is_set():
        imap = get_imap_connection(config)
        if imap is None or exit_event.is_set():
            exit(1)

        bons = list()
        for Adapter_cls in all_search_adapters:
            if config.is_adapter_enabled(Adapter_cls.adapter_name()):
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
    click.echo("Categories  (Used for  COSPEND_CATEGORYID_... )")
    click.echo("----------")
    for key, val in project_infos.categories.items():
        click.echo(f"  - {key}: {val.name} {val.icon}")
    click.echo("")
    click.echo("Payment Modes  (Used for  COSPEND_PAYMENTMODEID_... )")
    click.echo("-------------")
    for key, val in project_infos.paymentmodes.items():
        click.echo(f"  - {key}: {val.name} {val.icon}")
    click.echo("")
    click.echo("Members  (Used for  COSPEND_PAYED_FOR_...  (multiple seperated by a ',') and  COSPEND_PAYER_... )")
    click.echo("-------")
    for key, val in project_infos.members.items():
        click.echo(f"  - {key}: {val.name}")
