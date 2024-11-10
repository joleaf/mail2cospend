import dataclasses
import datetime
import logging
import os

from dotenv import load_dotenv


@dataclasses.dataclass(frozen=True)
class Config:
    cospend_project_url: str
    cospend_payed_for: str
    cospend_payer: str
    cospend_categoryid_default: int
    cospend_paymentmodeid_default: int
    imap_host: str
    imap_user: str
    imap_password: str
    imap_inbox: str
    interval: int
    since: str

    def get_since_for_imap_query(self):
        if self.since == "today":
            since_dt = datetime.datetime.today()
        else:
            since_dt = datetime.datetime.fromisoformat(self.since)
        return since_dt.strftime("%d-%b-%Y")


def load_config() -> Config:
    load_dotenv()
    config = Config(
        cospend_project_url=os.environ.get('COSPEND_PROJECT_URL'),
        cospend_payed_for=os.environ.get('COSPEND_PAYED_FOR') or "1",
        cospend_payer=os.environ.get('COSPEND_PAYER') or "1",
        cospend_categoryid_default=int(os.environ.get('COSPEND_CATEGORYID_DEFAULT')) or "1",
        cospend_paymentmodeid_default=int(os.environ.get('COSPEND_PAYMENTMODEID_DEFAULT')) or "1",
        imap_host=os.environ.get('IMAP_HOST'),
        imap_user=os.environ.get('IMAP_USER'),
        imap_password=os.environ.get('IMAP_PASSWORD'),
        imap_inbox=os.environ.get('IMAP_INBOX') or 'Inbox',
        interval=int(os.environ.get('INTERVAL')) or 60,
        since=os.environ.get('SINCE') or 'today'
    )
    return config
