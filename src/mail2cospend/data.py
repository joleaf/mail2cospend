import dataclasses
from datetime import datetime


@dataclasses.dataclass(frozen=True)
class BonSummary:
    timestamp: datetime
    sum: float
    beleg: str
    adapter_name: str

    def get_id(self):
        return self.adapter_name + "_" + self.timestamp.isoformat() + "_" + self.beleg
