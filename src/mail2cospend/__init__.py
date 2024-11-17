import logging
import signal
from pprint import pformat

import click

from mail2cospend.config import load_config
from mail2cospend.main import run as main_run, exit_event, print_cospend_project_infos


def quit(signo, _frame):
    logging.info("Interrupted by %d, shutting down" % signo)
    exit_event.set()


@click.group()
@click.version_option()
def cli():
    signal.signal(signal.SIGTERM, quit)
    signal.signal(signal.SIGINT, quit)
    signal.signal(signal.SIGHUP, quit)


@cli.command(
    help='Only print information about the cospend project (Category, Payer IDs, Payment mode,..) and then exit the program.')
def project_infos():
    print_cospend_project_infos()


@cli.command(help='Run the service. Request the bons and publish them to the server.')
def run():
    main_run()


@cli.command(help='Dry run without publishing to the cospend server.')
def dry_run():
    main_run(dry=True)


@cli.command(help='Print the current config.')
def show_config():
    config = load_config(None)
    logging.info(pformat(config))
