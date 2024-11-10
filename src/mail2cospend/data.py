import dataclasses
from datetime import datetime


@dataclasses.dataclass(frozen=True)
class BonSummary:
    timestamp: datetime
    sum: float
    beleg: str
    type: str

    def get_id(self):
        return self.type + "_" + self.timestamp.isoformat() + "_" + self.beleg
