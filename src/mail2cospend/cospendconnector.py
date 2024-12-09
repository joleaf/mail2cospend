import dataclasses
import datetime
import enum
import logging
from dataclasses import field
from typing import List, Dict

import requests

from mail2cospend.config import Config
from mail2cospend.data import BonSummary
from mail2cospend.helper import add_published_id


@dataclasses.dataclass(frozen=True)
class Member:
    id: int
    activated: bool
    color: str
    name: str
    weight: float


@dataclasses.dataclass(frozen=True)
class Category:
    id: int
    color: str
    icon: str
    name: str
    order: int


@dataclasses.dataclass(frozen=True)
class PaymentMode:
    id: int
    color: str
    icon: str
    name: str
    order: int


@dataclasses.dataclass(frozen=True)
class CospendProjectInfos:
    categories: Dict[int, Category] = field(default_factory=dict)
    paymentmodes: Dict[int, PaymentMode] = field(default_factory=dict)
    members: Dict[int, Member] = field(default_factory=dict)


def test_connection(config: Config):
    url = _get_project_url(config, ApiType.INFOS)
    try:
        result = requests.get(url)
        if result.status_code < 400:
            logging.debug("Tested connection to the cospend project. Successful.")
            return True
        else:
            logging.error(
                f"No connection to the cospend project: {config.cospend_project_url}"
            )
            logging.error(f"{result.status_code}: {result.reason}")
            return False
    except:
        logging.error(
            f"No connection to the cospend project: {config.cospend_project_url}"
        )
        logging.error("Unknown error. Check url.")
        return False


def get_cospend_project_infos(config: Config) -> CospendProjectInfos:
    url = _get_project_url(config, ApiType.INFOS)
    result = requests.get(url)
    data = result.json()

    categories = dict()
    for key, val in data["categories"].items():
        categories[key] = Category(id=val["id"], color=val["color"], icon=val["icon"], name=val["name"],
                                   order=val["order"])

    paymentmodes = dict()
    for key, val in data["paymentmodes"].items():
        paymentmodes[key] = PaymentMode(id=val["id"], color=val["color"], icon=val["icon"], name=val["name"],
                                        order=val["order"])

    members = dict()
    for member in data["members"]:
        members[member['id']] = Member(id=member["id"], activated=member["activated"], color=member["color"],
                                       name=member["name"], weight=member["weight"])

    return CospendProjectInfos(categories, paymentmodes, members)


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
            logging.error(
                f"Waiting {seconds_to_wait} seconds for the next try. ({i}/{tries})"
            )
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
    if "api" not in url:
        url = url.replace("/cospend/s/", "/cospend/api/projects/")

    pw = config.cospend_project_password
    if pw is not None and len(pw) > 0:
        if api_type == ApiType.BILLS:
            url += f"{pw}/bills"
        elif api_type == ApiType.INFOS:
            url += f"{pw}"
    else:
        if api_type == ApiType.BILLS:
            url += "no-pass/bills"
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
            'what': bon.adapter_name,
            'payed_for': config.get_cospend_payed_for(bon.adapter_name),
            'payer': config.get_cospend_payer(bon.adapter_name),
            'timestamp': (bon.timestamp - datetime.datetime(1970, 1, 1)).total_seconds(),
            'categoryid': config.get_cospend_categoryid(bon.adapter_name),
            'paymentmodeid': config.get_cospend_paymentmodeid(bon.adapter_name),
            'comment': bon.adapter_name + ' - Autopush ' + (('- Beleg: ' + bon.document) if bon.document else '')
        }
        logging.debug(f"Publishing data: {str(data)} to url {url}")
        result = requests.post(url, json=data)
        if result.status_code < 400:
            add_published_id(bon)
            logging.debug(f"Published bon {bon} and added to published file")
            if config.ntfy_is_enabled:
                config.get_ntfy_client().publish_bon_summary(bon)

        else:
            logging.warning(f"Bon {bon} was not published to cospend!")
            logging.warning(f"{result.status_code}: {result.reason}")
