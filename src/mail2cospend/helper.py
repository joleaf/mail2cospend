import os
from typing import Set
from mail2cospend.data import BonSummary

publish_bong_ids: Set[str] = set()


def add_published_id(bon_summary: BonSummary):
    if not os.path.exists('data'):
        os.mkdir('data')
    with open(os.path.join("data", "published_ids.txt"), 'a') as f:
        f.write(bon_summary.get_id())
        f.write("\n")
        publish_bong_ids.add(bon_summary.get_id())


def get_published_ids() -> Set[str]:
    if len(publish_bong_ids) == 0:
        try:
            with open(os.path.join("data", "published_ids.txt"), 'r') as f:
                return {str(l).replace("\n", "") for l in f.readlines()}
        except FileNotFoundError:
            return publish_bong_ids
    return publish_bong_ids
