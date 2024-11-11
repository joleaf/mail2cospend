import logging
import signal

import click

from mail2cospend.main import run, exit_event, print_cospend_project_infos


def quit(signo, _frame):
    logging.info("Interrupted by %d, shutting down" % signo)
    exit_event.set()


@click.command()
@click.option('--dry/--no-dry', default=False, help='Dry run without publishing to the cospend server.')
@click.option('--project-infos/--no-project-infos', default=False,
              help='If enabled, only print information about the cospend project (Category, Payer IDs, Payment mode,..) and then exit the program.')
@click.version_option()
def cli(dry: bool, project_infos: bool):
    signal.signal(signal.SIGTERM, quit)
    signal.signal(signal.SIGINT, quit)
    signal.signal(signal.SIGHUP, quit)
    if project_infos:
        print_cospend_project_infos()
    else:
        run(dry=dry)
