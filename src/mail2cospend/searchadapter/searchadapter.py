import email
import imaplib
import logging
import os
from abc import ABC, abstractmethod
from datetime import datetime
from email import utils
from typing import List, Optional, Iterable

from PyPDF2 import PdfReader

from mail2cospend.data import BonSummary
from mail2cospend.helper import get_published_ids


class SearchAdapter(ABC):

    def __init__(self, config, imap: imaplib.IMAP4_SSL):
        self.config = config
        self.imap = imap

    @classmethod
    def adapter_name(cls) -> str:
        pass

    @classmethod
    def _use_pdf_in_mail(self) -> bool:
        pass

    @classmethod
    def _use_plain_text_in_mail(self) -> bool:
        pass

    @classmethod
    def _use_html_text_in_mail(self) -> bool:
        pass

    @property
    @abstractmethod
    def _search_query(self) -> str:
        pass

    @property
    def _coding(self) -> str:
        return 'utf-8'

    def search(self) -> List[BonSummary]:
        published_ids = get_published_ids()
        search_query = self._search_query
        logging.info(f"Requesting {self.adapter_name()} from the mail server")
        logging.debug(f" search for: {search_query}")
        self.imap.select(self.config.imap_inbox)
        tmp, data = self.imap.search(None, search_query)
        result = []
        for num in data[0].split():
            typ, data = self.imap.fetch(num, '(RFC822)')
            raw_email = data[0][1]
            raw = email.message_from_bytes(data[0][1])
            email_timestamp = utils.parsedate_to_datetime(raw['date']).replace(tzinfo=None)
            raw_email_string = raw_email.decode('utf-8')
            msg = email.message_from_string(raw_email_string)
            # look for the mail part
            bon = None
            for part in msg.walk():
                if self._use_html_text_in_mail() and part.get_content_type() == 'text/html':
                    payload = part.get_payload(decode=True).decode(self._coding).split("\r\n")
                    bon = self._get_bon_from_text(payload, email_timestamp, is_html=True)
                    if bon is None:
                        logging.warning("Bon can not be parsed")
                if self._use_plain_text_in_mail() and part.get_content_type() == 'text/plain':
                    payload = part.get_payload(decode=True).decode(self._coding).split("\r\n")
                    bon = self._get_bon_from_text(payload, email_timestamp, is_html=False)
                    if bon is None:
                        logging.warning("Bon can not be parsed")
                if (self._use_pdf_in_mail()
                        and (
                                part.get_content_type() == 'application/octet-stream'
                                or part.get_content_type() == 'application/pdf'
                        )):

                    # When decode=True, get_payload will return None if part.is_multipart()
                    # and the decoded content otherwise.
                    payload = part.get_payload(decode=True)

                    # Default filename can be passed as an argument to get_filename()
                    filename = part.get_filename()

                    # Save the file.
                    if payload and filename:
                        with open(filename, 'wb') as f:
                            f.write(payload)
                        try:
                            pdf = PdfReader(open(filename, 'rb'))
                            bon = self._get_bon_from_pdf(pdf, email_timestamp)
                        except:
                            pass
                        os.remove(filename)
                        if bon is None:
                            logging.warning("Bon can not be parsed")
                if bon is not None:
                    break
            if bon is not None:
                if bon.get_id() in published_ids:
                    logging.debug(f"Skipping ID {bon.get_id()} ({self.adapter_name()}), already published!")
                else:
                    result.append(bon)
        logging.debug(f"Found {len(result)} bons")
        return result

    @abstractmethod
    def _get_bon_from_pdf(self, pdf: PdfReader, email_timestamp: datetime) -> Optional[BonSummary]:
        return None

    @abstractmethod
    def _get_bon_from_text(self, payload: Iterable[str], email_timestamp: datetime, is_html: bool) -> Optional[
        BonSummary]:
        return None
