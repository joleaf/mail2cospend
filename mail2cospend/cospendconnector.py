import datetime
import logging
from time import sleep
from typing import List

import requests

from mail2cospend.config import Config
from mail2cospend.data import BonSummary
from mail2cospend.helper import add_published_id


def publish_bongs(bons: List[BonSummary], config: Config):
    tries = 8
    for i in range(tries):
        try:
            _try_publish_bons(bons, config)
            break
        except:
            logging.error("No connection to the cospend server.")
            seconds_to_wait = config.interval * 2 ** i
            logging.error(f"Waiting {seconds_to_wait} seconds for the next try. ({i}/{tries})")
            sleep(seconds_to_wait)
            if i == tries - 1:
                exit(1)


def _try_publish_bons(bons: List[BonSummary], config: Config):
    if len(bons) > 0:
        logging.info(f"Found {len(bons)} bons")
    for bon in bons:
        logging.info(f"Pushing new bill: {bon}")
        url = config.cospend_project_url
        if not url.endswith("/"):
            url += "/"
        url += "no-pass/bills"

        data = {
            'amount': bon.sum,
            'what': bon.type,
            'payed_for': config.cospend_payed_for,
            'payer': '3',
            'timestamp': (bon.timestamp - datetime.datetime(1970, 1, 1)).total_seconds(),
            'categoryid': config.cospend_categoryid_default,
            'paymentmodeid': config.cospend_paymentmodeid_default,
            'comment': bon.type + ' - Autopush - Beleg: ' + bon.beleg
        }
        logging.debug(f"Sending data: {str(data)}")
        result = requests.post(url, json=data)
        if result.status_code < 400:
            logging.debug("Add bon {bon} to published file")
            add_published_id(bon)
        else:
            logging.warning("Bon {bon} was not published to cospend!")
            logging.warning(f"{result.status_code}: {result.reason}")
