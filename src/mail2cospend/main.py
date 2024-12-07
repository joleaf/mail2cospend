import logging
from threading import Event
from typing import Optional, Dict, List

from mail2cospend.config import load_config, Config
from mail2cospend.cospendconnector import publish_bongs, test_connection, get_cospend_project_infos, \
    get_cospend_project_statistics, CospendProjectInfos
from mail2cospend.mailconnector import get_imap_connection
from mail2cospend.searchadapter import all_search_adapters

exit_event = Event()


def _init() -> Config:
    config = load_config(exit_event)

    if not test_connection(config):
        exit(1)
    return config


def run(dry=False):
    config = _init()
    logging.debug("Enabled adapters:")
    for adapter in all_search_adapters:
        if config.is_adapter_enabled(adapter.adapter_name()):
            logging.debug(f"  - {adapter.adapter_name()}")

    while not exit_event.is_set():
        imap = get_imap_connection(config)
        if imap is None or exit_event.is_set():
            exit(1)

        bons = list()
        for Adapter_cls in all_search_adapters:
            if config.is_adapter_enabled(Adapter_cls.adapter_name()):
                adapter = Adapter_cls(config, imap)
                this_bons = adapter.search()
                bons += this_bons
                imap.close()
        imap.shutdown()

        if exit_event.is_set():
            exit(1)

        if dry:
            logging.info("Dry run. Results:")
            for bon in bons:
                logging.info(bon)
            break
        else:
            publish_bongs(bons, config)
        if exit_event.is_set():
            exit(1)
        logging.info(f"Waiting {config.interval} seconds before next run")
        exit_event.wait(config.interval)


def print_cospend_project_infos():
    config = _init()
    project_infos = get_cospend_project_infos(config)
    print("Categories  (Used for  COSPEND_CATEGORYID_... )")
    print("----------")
    for key, val in project_infos.categories.items():
        print(f"  - {key}: {val.name} {val.icon}")
    print("")
    print("Payment Modes  (Used for  COSPEND_PAYMENTMODEID_... )")
    print("-------------")
    for key, val in project_infos.paymentmodes.items():
        print(f"  - {key}: {val.name} {val.icon}")
    print("")
    print("Members  (Used for  COSPEND_PAYED_FOR_...  (multiple seperated by a ',') and  COSPEND_PAYER_... )")
    print("-------")
    for key, val in project_infos.members.items():
        print(f"  - {key}: {val.name}")


def print_cospend_project_statistics(year_month: Optional[str] = None):
    config = _init()
    logging.error(year_month)
    if year_month is None:
        year_month = datetime.now().strftime("%Y-%m")
    project_statistics = get_cospend_project_statistics(config, year_month)
    project_infos = get_cospend_project_infos(config)
    result_string = _get_cospend_project_one_month_statistics_strings(project_statistics, project_infos, year_month)
    for line in result_string:
        print(line)


def _get_cospend_project_one_month_statistics_strings(project_statistics: Dict,
                                                      project_infos: CospendProjectInfos,
                                                      year_month: str,
                                                      print_icons: bool = False,
                                                      add_bar=True) -> List[str]:
    result = []
    pprint.pprint(project_statistics)
    result.append(f"Statistics for {year_month}")
    result.append("")
    result.append("Categories")
    result.append("----------")
    maxVal = max(
        val.get(year_month, 0) for key, val in project_statistics['categoryMonthlyStats'].items() if
        project_infos.categories.get(key))
    for key, val in project_statistics['categoryMonthlyStats'].items():
        if project_infos.categories.get(key):
            val = val.get(year_month, 0)
            if val > 0:
                ico_s = ""
                if print_icons:
                    ico_s = f" {project_infos.categories[key].icon}"
                result.append(
                    f" -{ico_s} {project_infos.categories[key].name:<40}: {val:9.2f}€")
                if add_bar:
                    result[-1] += "  |" + ("#" * (int((val / maxVal) * 40))) + (
                                " " * (40 - int((val / maxVal) * 40))) + "|"
    result.append("")
    result.append("Payment Modes")
    result.append("-------------")
    maxVal = max(
        val.get(year_month, 0) for key, val in project_statistics['paymentModeMonthlyStats'].items() if
        project_infos.paymentmodes.get(key))
    for key, val in project_statistics['paymentModeMonthlyStats'].items():
        if project_infos.paymentmodes.get(key):
            val = val.get(year_month, 0)
            if val > 0:
                ico_s = ""
                if print_icons:
                    ico_s = f" {project_infos.paymentmodes[key].icon}"
                result.append(
                    f" -{ico_s} {project_infos.paymentmodes[key].name:<40}: {val:9.2f}€")
                if add_bar:
                    result[-1] += "  |" + ("#" * (int((val / maxVal) * 40))) + (
                                " " * (40 - int((val / maxVal) * 40))) + "|"

    return result
