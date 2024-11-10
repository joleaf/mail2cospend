import datetime
from abc import ABC
from typing import Iterable, Optional

from PyPDF2 import PdfReader

from mail2cospend.data import BonSummary
from mail2cospend.searchadapter.searchadapter import SearchAdapter


class ReweSearchAdapter(SearchAdapter):

    @classmethod
    def adapter_name(cls) -> str:
        return "Rewe eBon"

    @classmethod
    def _use_pdf_in_mail(cls) -> bool:
        return True

    @classmethod
    def _use_plain_text_in_mail(cls) -> bool:
        return False

    @classmethod
    def _use_html_text_in_mail(self) -> bool:
        return False

    @property
    def _search_query(self) -> str:
        return f'(SUBJECT "REWE eBon") (SINCE "{self.config.get_since_for_imap_query()}")'

    def _get_bon_from_pdf(self, pdf: PdfReader, email_timestamp: datetime.datetime) -> Optional[BonSummary]:
        sum = [float(l.replace(",", ".").replace("SUMME", "").replace("EUR", "").strip())
               for page in pdf.pages
               for l in page.extract_text().split("\n")
               if "SUMME" in l][0]
        datarow = [l.strip().split("     ")
                   for page in pdf.pages
                   for l in page.extract_text().split("\n")
                   if "Bon-Nr." in l][0]
        day, month, year = map(int, datarow[0].split("."))
        hour, minute = map(int, datarow[1].split(":"))
        beleg = datarow[2]
        timestamp = datetime.datetime(year=year, month=month, day=day, hour=hour, minute=minute)

        bon = BonSummary(sum=sum, beleg=beleg, timestamp=timestamp, type="Rewe")
        return bon

    def _get_bon_from_plain_text(self, payload: Iterable[str], email_timestamp: datetime) -> Optional[BonSummary]:
        return None

    def _get_bon_from_html_text(self, payload: Iterable[str], email_timestamp: datetime) -> Optional[BonSummary]:
        return None
