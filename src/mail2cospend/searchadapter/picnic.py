from datetime import datetime
from typing import Iterable, Optional

from PyPDF2 import PdfReader

from mail2cospend.data import BonSummary
from mail2cospend.searchadapter.searchadapter import SearchAdapter


class PicnicSearchAdapter(SearchAdapter):

    @classmethod
    def adapter_name(cls) -> str:
        return "Picnic"

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
        return f'(FROM info@mail.picnic.de) (SUBJECT "Dein Bon") (SINCE "{self.config.get_since_for_imap_query()}")'

    def _coding(self) -> str:
        return 'latin-1'

    def _get_bon_from_pdf(self, pdf: PdfReader, email_timestamp: datetime) -> Optional[BonSummary]:
        return None

    def _get_bon_from_text(self, payload: Iterable[str], email_timestamp: datetime, is_html: bool) -> Optional[
        BonSummary]:
        sum = 0
        # beleg = payload[1] + " " + payload[5]
        for row in payload:
            if "Gesamtbetrag" in row:
                sum = float(row.split()[1].replace("..", "."))
        bon = BonSummary(sum=sum, document="", timestamp=email_timestamp, adapter_name=self.adapter_name())
        return bon
