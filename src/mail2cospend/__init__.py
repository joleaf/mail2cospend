import logging
import signal

import click

from mail2cospend.main import run, exit_event


def quit(signo, _frame):
    logging.info("Interrupted by %d, shutting down" % signo)
    exit_event.set()


@click.command()
@click.option('--dry/--no-dry', default=False, help='Dry run without publishing to the cospend server.')
@click.version_option()
def cli(dry: bool):
    signal.signal(signal.SIGTERM, quit)
    signal.signal(signal.SIGINT, quit)
    signal.signal(signal.SIGHUP, quit)
    run(dry=dry)
