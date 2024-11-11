import dataclasses
import datetime
import enum
import logging
from dataclasses import field
from typing import List

import requests

from mail2cospend.config import Config
from mail2cospend.data import BonSummary
from mail2cospend.helper import add_published_id


@dataclasses.dataclass(frozen=True)
class CospendProjectInfos:
    categories: List[str] = field(default_factory=list)
    paymentmodes: List[str] = field(default_factory=list)
    members: List[str] = field(default_factory=list)


def test_connection(config: Config):
    url = _get_project_url(config, ApiType.INFOS)
    try:
        result = requests.get(url)
        if result.status_code < 400:
            logging.debug("Tested connection to the cospend project. Successful.")
            return True
        else:
            logging.error(f"No connection to the cospend project: {config.cospend_project_url}")
            logging.error(f"{result.status_code}: {result.reason}")
            return False
    except:
        logging.error(f"No connection to the cospend project: {config.cospend_project_url}")
        logging.error("Unknown error. Check url.")
        return False


def get_cospend_project_infos(config: Config) -> CospendProjectInfos:
    url = _get_project_url(config, ApiType.INFOS)
    result = requests.get(url)
    data = result.json()

    categories = list()
    for key, val in data["categories"].items():
        categories.append(f"{key}: {val['name']}")

    paymentmodes = list()
    for key, val in data["paymentmodes"].items():
        paymentmodes.append(f"{key}: {val['name']}")

    members = list()
    for member in data["members"]:
        members.append(f"{member['id']}: {member['name']}")

    return CospendProjectInfos(
        categories,
        paymentmodes,
        members
    )


def publish_bongs(bons: List[BonSummary], config: Config):
    tries = 10
    for i in range(tries):
        if config.exit_event.is_set():
            break
        try:
            _try_publish_bons(bons, config)
            break
        except:
            logging.error("No connection to the cospend server.")
            seconds_to_wait = config.interval * 2 ** i
            logging.error(f"Waiting {seconds_to_wait} seconds for the next try. ({i}/{tries})")
            config.exit_event.wait(seconds_to_wait)
            if i == tries - 1:
                exit(1)


class ApiType(enum.Enum):
    BILLS = 1
    INFOS = 2


def _get_project_url(config: Config, api_type: ApiType) -> str:
    url = config.cospend_project_url
    if not url.endswith("/"):
        url += "/"
    # Convert the "project" url into the api url
    if 'api' not in url:
        url = url.replace("/cospend/s/", "/cospend/api/projects/")

    pw = config.cospend_project_password
    if pw is not None and len(pw) > 0:
        if api_type == ApiType.BILLS:
            url += f"{pw}/bills"
        elif api_type == ApiType.INFOS:
            url += f"{pw}"
    else:
        if api_type == ApiType.BILLS:
            url += "bills"
        elif api_type == ApiType.INFOS:
            url += "members"
    return url


def _try_publish_bons(bons: List[BonSummary], config: Config):
    if len(bons) > 0:
        logging.info(f"Found {len(bons)} bons")
    for bon in bons:
        logging.info(f"Pushing new bill: {bon}")
        url = _get_project_url(config, ApiType.BILLS)

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
        logging.debug(f"Sending data: {str(data)} to url {url}")
        result = requests.post(url, json=data)
        if result.status_code < 400:
            add_published_id(bon)
            logging.debug(f"Published bon {bon} and added to published file")
        else:
            logging.warning(f"Bon {bon} was not published to cospend!")
            logging.warning(f"{result.status_code}: {result.reason}")
