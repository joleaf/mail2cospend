import dataclasses
from datetime import datetime


@dataclasses.dataclass(frozen=True)
class BonSummary:
    timestamp: datetime
    sum: float
    document: str
    adapter_name: str

    def get_id(self):
        return self.adapter_name + "_" + self.timestamp.isoformat() + "_" + self.document

    def as_pretty_string(self, template: str) -> str:
        return template \
            .replace("{adapter}", self.adapter_name) \
            .replace("{timestamp}", self.timestamp.strftime("%Y-%m-%d %H:%M:%S")) \
            .replace("{document}", self.document) \
            .replace("{sum}", f"{self.sum:.2f}")
