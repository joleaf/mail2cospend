from datetime import datetime
from typing import Iterable, Optional, overload, override

from PyPDF2 import PdfReader

from mail2cospend.data import BonSummary
from mail2cospend.searchadapter.searchadapter import SearchAdapter


class PicnicSearchAdapter(SearchAdapter):

    @classmethod
    def adapter_name(cls) -> str:
        return "Picnic eBon"

    @classmethod
    def _use_pdf_in_mail(cls) -> bool:
        return False

    @classmethod
    def _use_plain_text_in_mail(cls) -> bool:
        return True

    @classmethod
    def _use_html_text_in_mail(self) -> bool:
        return False

    @property
    def _search_query(self) -> str:
        return f'(SUBJECT "Dein Bon") (SINCE "{self.config.get_since_for_imap_query()}")'

    def _get_bon_from_pdf(self, pdf: PdfReader, email_timestamp: datetime) -> Optional[BonSummary]:
        return False

    def _get_bon_from_plain_text(self, payload: Iterable[str], email_timestamp: datetime) -> Optional[BonSummary]:
        sum = 0
        # beleg = payload[1] + " " + payload[5]
        for row in payload:
            if "Gesamtbetrag" in row:
                sum = float(row.split()[1].replace("..", "."))
        bon = BonSummary(sum=sum, beleg="", timestamp=email_timestamp, type="PicNic")
        return bon

    def _get_bon_from_html_text(self, payload: Iterable[str], email_timestamp: datetime) -> Optional[BonSummary]:
        return None