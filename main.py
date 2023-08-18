import dataclasses
import datetime
import imaplib
import email
import os
from time import sleep
from typing import List, Optional
from dotenv import load_dotenv
import requests
import PyPDF2
import logging

logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p',
                    level=logging.DEBUG)


@dataclasses.dataclass
class ReweBonSummary:
    timestamp: datetime.datetime
    sum: float
    beleg: str

    def get_id(self):
        return self.timestamp.isoformat() + "/" + self.beleg


def run():
    config = load_config()
    while 1:
        imap = None
        # Try to open a connection x times
        tries = 8
        for i in range(tries):
            try:
                imap = connect_imap(config)
                break
            except:
                logging.error("No connection to the imap server.")
                seconds_to_wait = config['interval'] * 2 ** i
                logging.error(f"Waiting {seconds_to_wait} seconds for the next try.")
                sleep(seconds_to_wait)
                if i == tries - 1:
                    exit(1)
        new_rewe_bons = search_rewe_ebons(imap, config)
        imap.close()
        for i in range(tries):
            try:
                publish_rewe_bons(new_rewe_bons, config)
                break
            except:
                logging.error("No connection to the cospend server.")
                seconds_to_wait = config['interval'] * 2 ** i
                logging.error(f"Waiting {seconds_to_wait} seconds for the next try.")
                sleep(seconds_to_wait)
                if i == tries - 1:
                    exit(1)
        sleep(config['interval'])


def load_config() -> dict[str, str | int]:
    load_dotenv()
    config = {
        'imap_host': os.environ.get('imap_host'),
        'imap_user': os.environ.get('imap_user'),
        'imap_pass': os.environ.get('imap_pass'),
        'since': os.environ.get('since', 'today'),  # Format: dd-Mon-yyyy  (e.g. '14 - Aug - 2014') or 'today'
        'interval': int(os.environ.get('interval', '60')),  # in seconds
    }
    return config


def connect_imap(config) -> imaplib.IMAP4_SSL:
    imap_host = config['imap_host']
    imap_user = config['imap_user']
    imap_pass = config['imap_pass']
    # connect to host using SSL
    imap = imaplib.IMAP4_SSL(imap_host)
    # login to server
    imap.login(imap_user, imap_pass)
    return imap


def search_rewe_ebons(imap, config) -> List[ReweBonSummary]:
    published_ids = set(get_published_ids())
    since = config.get('since', 'today')
    if since == "today":
        since = datetime.datetime.today().strftime("%d-%b-%Y")

    search_query = f'(SUBJECT "REWE eBon") (SINCE {since})'
    logging.debug(f"Search for: {search_query}")
    imap.select("Inbox")
    tmp, data = imap.search(None, search_query)
    result = []
    for num in data[0].split():
        typ, data = imap.fetch(num, '(RFC822)')
        raw_email = data[0][1]
        raw_email_string = raw_email.decode('utf-8')
        msg = email.message_from_string(raw_email_string)
        # look for the pdf
        for part in msg.walk():
            if part.get_content_type() == 'application/octet-stream':
                # When decode=True, get_payload will return None if part.is_multipart()
                # and the decoded content otherwise.
                payload = part.get_payload(decode=True)

                # Default filename can be passed as an argument to get_filename()
                filename = part.get_filename()

                # Save the file.
                if payload and filename:
                    with open(filename, 'wb') as f:
                        f.write(payload)

                    rewe_bon_summery = parse_pdf_to_rewe_bon_summary(filename)
                    if rewe_bon_summery == None:
                        logging.warning(f"Rewe Bon can not be parsed")
                    elif rewe_bon_summery.get_id() in published_ids:
                        logging.debug(f"Skipping ID {rewe_bon_summery.get_id()}, already published")
                    else:
                        result.append(rewe_bon_summery)

    return result


def parse_pdf_to_rewe_bon_summary(filename) -> Optional[ReweBonSummary]:
    try:
        pdf = PyPDF2.PdfReader(open(filename, 'rb'))
        sum = [float(l.replace(",", ".").replace("SUMME", "").replace("EUR", "").strip())
               for page in pdf.pages
               for l in page.extract_text().split("\n")
               if "SUMME" in l][0]
        day, month, year = map(int, [l.replace("Datum:", "").strip()
                                     for page in pdf.pages
                                     for l in page.extract_text().split("\n")
                                     if "Datum:" in l][0].split("."))
        hour, minute, second = map(int, [l.replace("Uhrzeit:", "").replace("Uhr", "").strip()
                                         for page in pdf.pages
                                         for l in page.extract_text().split("\n")
                                         if "Uhrzeit:" in l][0].split(":"))
        beleg = [l.replace("Beleg-Nr.", "").strip()
                 for page in pdf.pages
                 for l in page.extract_text().split("\n")
                 if "Beleg-Nr." in l][0]
        timestamp = datetime.datetime(year=year, month=month, day=day, hour=hour, minute=minute,
                                      second=second)

        return ReweBonSummary(sum=sum, beleg=beleg, timestamp=timestamp)
    except:
        return None


def get_published_ids() -> List[str]:
    try:
        with open(os.path.join("data", "published_ids.txt"), 'r') as f:
            return [str(l).replace("\n", "") for l in f.readlines()]
    except FileNotFoundError:
        return []


def add_published_id(rewe_bon_summary: ReweBonSummary):
    if not os.path.exists('data'):
        os.mkdir('data')
    with open(os.path.join("data", "published_ids.txt"), 'a') as f:
        f.write(rewe_bon_summary.get_id())
        f.write("\n")


def publish_rewe_bons(rewe_bons: List[ReweBonSummary], config):
    if len(rewe_bons) > 0:
        logging.info(f"Found {len(rewe_bons)} bons")
    for rewe_bon in rewe_bons:
        url = 'https://cloud.jb-services.de/index.php/apps/cospend/api/projects/015f4519b2025896bbdfaf55702299cb/no-pass/bills'
        data = {
            'amount': rewe_bon.sum,
            'what': "Rewe",
            'payed_for': '1,2',
            'payer': '3',
            'timestamp': (rewe_bon.timestamp - datetime.datetime(1970, 1, 1)).total_seconds(),
            'categoryid': 1,
            'paymentmodeid': 1,
            'comment': 'Rewe Autopush - Beleg: ' + rewe_bon.beleg
        }
        logging.info(f"Pushing new bill: {rewe_bon}")
        logging.debug(str(data))
        result = requests.post(url, json=data)
        if result.status_code < 400:
            logging.debug("Add to published file")
            add_published_id(rewe_bon)
        else:
            logging.warning("Bill was not published to cospend!")
            logging.warning(f"{result.status_code}: {result.reason}")


if __name__ == '__main__':
    run()
