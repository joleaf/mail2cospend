import imaplib
from typing import Optional

from mail2cospend.config import Config
import logging


def _try_connect_imap(config) -> imaplib.IMAP4_SSL:
    imap_host = config.imap_host
    imap_user = config.imap_user
    imap_pass = config.imap_password
    imap_port = config.imap_port
    # connect to host using SSL
    imap = imaplib.IMAP4_SSL(imap_host, imap_port)
    # login to server
    imap.login(imap_user, imap_pass)
    return imap


def get_imap_connection(config: Config) -> Optional[imaplib.IMAP4_SSL]:
    imap = None
    # Try to open a connection x times
    tries = 10
    for i in range(1, tries + 1):
        if config.exit_event.is_set():
            break
        try:
            imap = _try_connect_imap(config)
            return imap
        except:
            logging.error("No connection to the imap server.")
            seconds_to_wait =  2 ** i
            logging.error(f"Waiting {seconds_to_wait} seconds for the next try. ({i}/{tries})")
            config.exit_event.wait(seconds_to_wait)
        if i == tries + 1:
            logging.error("Exited: No connection to the imap server.")
            break
    return None
