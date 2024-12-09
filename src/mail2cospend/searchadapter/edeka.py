from datetime import datetime
from typing import Iterable, Optional

from PyPDF2 import PdfReader

from mail2cospend.data import BonSummary
from mail2cospend.searchadapter.searchadapter import SearchAdapter


class EdekaSearchAdapter(SearchAdapter):

    @classmethod
    def adapter_name(cls) -> str:
        return "EDEKA"

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
        return f'(FROM noreply@app.edeka.de) (SUBJECT Vielen) (SINCE "{self.config.get_since_for_imap_query()}")'

    def _get_bon_from_pdf(self, pdf: PdfReader, email_timestamp: datetime) -> Optional[BonSummary]:
        data = [l.strip()
                for page in pdf.pages
                for l in page.extract_text().split("\n")]
        sum = [float(l.replace(",", ".").split()[2])
               for l in data
               if "SUMME" in l][0]
        beleg = [l.strip().split(" ")[-1]
                 for l in data
                 if "Beleg-Nr." in l][0]
        date = [l.strip().split(" ")[-1]
                for l in data
                if "Datum" in l][0]
        day, month, year = map(int, date.split("."))
        time = [l.strip().split(" ")[-2]
                for l in data
                if "Uhrzeit:" in l][0]
        hour, minute, second = map(int, time.split(":"))
        timestamp = datetime(year=year, month=month, day=day, hour=hour, minute=minute, second=second)

        bon = BonSummary(sum=sum, document=beleg, timestamp=timestamp, adapter_name=self.adapter_name())
        return bon

    def _get_bon_from_text(self, payload: Iterable[str], email_timestamp: datetime, is_html: bool) -> Optional[
        BonSummary]:
        return None
