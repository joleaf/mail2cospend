from datetime import datetime
from typing import Iterable, Optional

from PyPDF2 import PdfReader

from mail2cospend.data import BonSummary
from mail2cospend.searchadapter.searchadapter import SearchAdapter


class NettoSearchAdapter(SearchAdapter):

    @classmethod
    def adapter_name(cls) -> str:
        return "Netto"

    @classmethod
    def _use_pdf_in_mail(cls) -> bool:
        return False

    @classmethod
    def _use_plain_text_in_mail(cls) -> bool:
        return False

    @classmethod
    def _use_html_text_in_mail(self) -> bool:
        return True

    @property
    def _search_query(self) -> str:
        return f'(FROM noreply@netto-app.de) (SUBJECT "Marken-Discount!") (SINCE "{self.config.get_since_for_imap_query()}")'

    def _get_bon_from_pdf(self, pdf: PdfReader, email_timestamp: datetime) -> Optional[BonSummary]:
        return None

    def _get_bon_from_text(self, payload: Iterable[str], email_timestamp: datetime, is_html: bool) -> Optional[
        BonSummary]:
        found_summe = False
        sum = 0
        for row in payload:
            if "Summe:" in row:
                found_summe = True
                continue
            if found_summe:
                sum = float(row.split("<b>")[1].split(" ")[0].replace(",", "."))
                break
        bon = BonSummary(sum=sum, document="", timestamp=email_timestamp, adapter_name=self.adapter_name())
        return bon
