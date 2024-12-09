import dataclasses
import datetime
import logging
import os
from dataclasses import field
from threading import Event
from typing import Optional, Dict

from dotenv import load_dotenv

from mail2cospend.ntfy import Ntfy
from mail2cospend.searchadapter import all_search_adapters, SearchAdapter


@dataclasses.dataclass(frozen=True)
class Config:
    loglevel: str
    cospend_project_url: str
    cospend_project_password: Optional[str]
    cospend_payed_for_default: Optional[str]
    cospend_payer_default: Optional[str]
    cospend_categoryid_default: Optional[str]
    cospend_paymentmodeid_default: Optional[str]
    ntfy_url: Optional[str]
    ntfy_bearer_auth_token: Optional[str]
    ntfy_topic: str
    ntfy_message_template: str
    imap_host: str
    imap_user: str
    imap_password: str
    imap_inbox: str
    imap_port: int
    interval: int
    since: str
    exit_event: Event
    cospend_payed_for: Dict[str, str] = field(default_factory=dict)
    cospend_payer: Dict[str, str] = field(default_factory=dict)
    cospend_categoryids: Dict[str, str] = field(default_factory=dict)
    cospend_paymentmodeids: Dict[str, str] = field(default_factory=dict)
    adapter_enabled: Dict[str, bool] = field(default_factory=dict)

    def get_cospend_payed_for(self, adapter: SearchAdapter | str) -> str:
        if isinstance(adapter, SearchAdapter):
            adapter = adapter.adapter_name()
        return self.cospend_payed_for.get(adapter) or self.cospend_payed_for_default

    def get_cospend_payer(self, adapter: SearchAdapter | str) -> str:
        if isinstance(adapter, SearchAdapter):
            adapter = adapter.adapter_name()
        return self.cospend_payer.get(adapter) or self.cospend_payer_default

    def get_cospend_categoryid(self, adapter: SearchAdapter | str) -> str:
        if isinstance(adapter, SearchAdapter):
            adapter = adapter.adapter_name()
        return self.cospend_categoryids.get(adapter) or self.cospend_categoryid_default

    def get_cospend_paymentmodeid(self, adapter: SearchAdapter | str) -> str:
        if isinstance(adapter, SearchAdapter):
            adapter = adapter.adapter_name()
        return self.cospend_paymentmodeids.get(adapter) or self.cospend_paymentmodeid_default

    def is_adapter_enabled(self, adapter: SearchAdapter | str) -> bool:
        if isinstance(adapter, SearchAdapter):
            adapter = adapter.adapter_name()
        return self.adapter_enabled.get(adapter)

    def get_since_for_imap_query(self):
        if self.since == "today":
            since_dt = datetime.datetime.today()
        else:
            since_dt = datetime.datetime.fromisoformat(self.since)
        return since_dt.strftime("%d-%b-%Y")

    @property
    def ntfy_is_enabled(self):
        return self.ntfy_url is not None and self.ntfy_url != ""

    def get_ntfy_client(self) -> Ntfy:
        return Ntfy(self.ntfy_url, self.ntfy_topic, self.ntfy_message_template, self.ntfy_bearer_auth_token)


def load_config(exit_event: Event) -> Config:
    load_dotenv()
    loglevel = (os.environ.get('LOGLEVEL') or "INFO").upper()
    logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p',
                        level=loglevel)

    imap_port = _try_load_int_from_env('IMAP_PORT', 993)
    interval = _try_load_int_from_env('INTERVAL', 993)

    cospend_payed_for_default = os.environ.get('COSPEND_PAYED_FOR_DEFAULT')
    cospend_payed_for_adapter = _try_load_adapter_config('PAYED_FOR', cospend_payed_for_default)
    cospend_payer_default = os.environ.get('COSPEND_PAYER_DEFAULT')
    cospend_payer_adapter = _try_load_adapter_config('PAYER', cospend_payer_default)
    cospend_categoryid_default = os.environ.get('COSPEND_CATEGORYID_DEFAULT')
    cospend_categoryid_adapter = _try_load_adapter_config('CATEGORYID', cospend_categoryid_default)
    cospend_paymentmodeid_default = os.environ.get('COSPEND_PAYMENTMODEID_DEFAULT')
    cospend_paymentmodeid_adapter = _try_load_adapter_config('PAYMENTMODEID', cospend_categoryid_default)
    adapter_enabled = dict()
    for adapter in all_search_adapters:
        full_key = f"ADAPTER_{adapter.adapter_name().upper()}_ENABLED"
        value = os.environ.get(full_key)
        if value:
            value = value.lower() not in "false,0,disabled,off".split(",")
        else:
            value = True
        adapter_enabled[adapter.adapter_name()] = value

    since = os.environ.get('SINCE') or 'today'
    if since != "today":
        try:
            datetime.datetime.fromisoformat(since)
        except:
            logging.error(f"Since date must be a valued isoformat string: was '{since}'")
            exit(1)

    config = Config(
        loglevel=loglevel,
        cospend_project_url=os.environ.get('COSPEND_PROJECT_URL'),
        cospend_project_password=os.environ.get('COSPEND_PROJECT_PASSWORD'),
        cospend_payed_for_default=cospend_payed_for_default,
        cospend_payer_default=cospend_payer_default,
        cospend_categoryid_default=cospend_categoryid_default,
        cospend_paymentmodeid_default=cospend_paymentmodeid_default,
        imap_host=os.environ.get('IMAP_HOST'),
        imap_user=os.environ.get('IMAP_USER'),
        imap_password=os.environ.get('IMAP_PASSWORD'),
        imap_inbox=os.environ.get('IMAP_INBOX') or 'Inbox',
        imap_port=imap_port,
        interval=interval,
        since=since,
        exit_event=exit_event,
        cospend_payed_for=cospend_payed_for_adapter,
        cospend_payer=cospend_payer_adapter,
        cospend_categoryids=cospend_categoryid_adapter,
        cospend_paymentmodeids=cospend_paymentmodeid_adapter,
        ntfy_url=os.environ.get('NTFY_URL'),
        ntfy_bearer_auth_token=os.environ.get('NTFY_BEARER_AUTH_TOKEN'),
        ntfy_topic=os.environ.get('NTFY_TOPIC') or "mail2cospend",
        ntfy_message_template=os.environ.get('NTFY_MESSAGE_TEMPLATE') or "{sum}€ {adapter}/{document} ({timestamp})",
        adapter_enabled=adapter_enabled,
    )

    return config


def _try_load_int_from_env(field: str, default: Optional[int] = None) -> Optional[int]:
    try:
        val = os.environ.get(field)
        if val is not None and val != "":
            val = int(val)
        else:
            val = default
    except:
        logging.error(f"Environment parameter '{field}' is not an integer. Was '{os.environ.get(field)}'")
        exit(1)
    return val


def _try_load_adapter_config(key: str, default: str) -> Dict[str, str]:
    result = dict()
    for adapter in all_search_adapters:
        full_key = f"COSPEND_{key}_{adapter.adapter_name().upper()}"
        value = os.environ.get(full_key) or default
        result[adapter.adapter_name()] = value
    return result
