import logging
from typing import Optional

import requests

from mail2cospend.data import BonSummary


class Ntfy:

    def __init__(self, url: str, topic: str, message_template: str, bearer_auth_token: Optional[str] = None):
        self.url = url
        if not self.url.endswith("/"):
            self.url += "/"
        self.topic = topic
        self.message_template = message_template
        self.bearer_auth_token = bearer_auth_token
        assert self.url is not None
        assert self.topic is not None
        assert self.message_template is not None

    def publish_bon_summary(self, bon_summary: BonSummary):
        try:
            requests.post(url=self.url + self.topic,
                          data=bon_summary.as_pretty_string(self.message_template).encode(encoding='utf-8'),
                          headers=self._get_header()
                          )
        except Exception as e:
            logging.error(e)
            logging.error(f"No connection to NTFY: {self.url} with topic {self.topic}")

    def _get_header(self) -> dict:
        headers = {}
        if self.bearer_auth_token is not None and self.bearer_auth_token != "":
            headers = {
                "Authorization": f"Bearer {self.bearer_auth_token}"
            }
        return headers
