from datetime import datetime
from typing import Iterable, Optional

from PyPDF2 import PdfReader

from mail2cospend.data import BonSummary
from mail2cospend.searchadapter.searchadapter import SearchAdapter


class IkeaSearchAdapter(SearchAdapter):

    @classmethod
    def adapter_name(cls) -> str:
        return "IKEA"

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
        return f'(FROM information@cm.order.email.ikea.com) (SUBJECT "Rechnung") (SINCE "{self.config.get_since_for_imap_query()}")'

    @property
    def _coding(self) -> str:
        return 'utf-8'

    def _get_bon_from_pdf(self, pdf: PdfReader, email_timestamp: datetime) -> Optional[BonSummary]:
        data = [l.strip()
                for page in pdf.pages
                for l in page.extract_text().split("\n")]
        sum = [float(l.replace(",", ".").split()[-1])
               for l in data
               if "Gesamtsumme:" in l][0]
        beleg = [l.strip().split(" ")[-1]
                 for l in data
                 if "Rechnungsnummer:" in l][0]
        date = [l.strip().split(" ")[-1]
                for l in data
                if "Rechnungsdatum:" in l][0]
        day, month, year = map(int, date.split("."))

        timestamp = datetime(year=year, month=month, day=day)

        bon = BonSummary(sum=sum, document=beleg, timestamp=timestamp, adapter_name=self.adapter_name())
        return bon

    def _get_bon_from_text(self, payload: Iterable[str], email_timestamp: datetime, is_html: bool) -> Optional[
        BonSummary]:
        return None
