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

from email import utils

logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p',
                    level=logging.DEBUG)


@dataclasses.dataclass
class BonSummary:
    timestamp: datetime.datetime
    sum: float
    beleg: str
    type: str

    def get_id(self):
        return self.type + "_" + self.timestamp.isoformat() 


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
        bons = list()
        #bons += search_rewe_ebons(imap, config)
        
        bons += search_picnic_ebons(imap, config)
        
        imap.close()
        for i in range(tries):
            try:
                publish_bons(bons, config)
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
        'since': os.environ.get('since', 'today'),  # Format: dd-Mon-yyyy  (e.g. '14- Aug-2014') or 'today'
        'interval': int(os.environ.get('interval', '60')),  # in seconds
    }
    since = config.get('since')
    if since == "today":
        since = datetime.datetime.today().strftime("%d-%b-%Y")
    config['since'] = since
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


def search_rewe_ebons(imap, config) -> List[BonSummary]:
    published_ids = set(get_published_ids())
    search_query = f'(SUBJECT "REWE eBon") (SINCE {config["since"]})'
    logging.info("Requesting Rewe eBons from the mail server")
    logging.debug(f" search for: {search_query}")
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

def search_picnic_ebons(imap, config) -> List[BonSummary]:
    published_ids = set(get_published_ids())
    search_query = f'(SUBJECT "Dein Bon") (SINCE {config["since"]})'
    logging.info("Requesting PicNic Bons from the mail server")
    logging.debug(f" search for: {search_query}")
    imap.select("Inbox")
    tmp, data = imap.search(None, search_query)
    result = []
    for num in data[0].split():
        typ, data = imap.fetch(num, '(RFC822)')
        raw_email = data[0][1]
        raw = email.message_from_bytes(data[0][1])
        timestamp = utils.parsedate_to_datetime(raw['date']).replace(tzinfo=None)
        raw_email_string = raw_email.decode('utf-8')
        msg = email.message_from_string(raw_email_string)
        beleg = ""
        for part in msg.walk():
            if part.get_content_type() != 'text/plain':
                continue
            payload = part.get_payload(decode=True).decode('latin-1').split("\r\n")
            sum = 0
            #beleg = payload[1] + " " + payload[5]
            for row in payload:
                if "Gesamtbetrag" in row:
                    sum = float(row.split()[1].replace("..","."))
        bon_summary = BonSummary(sum=sum, beleg=beleg, timestamp=timestamp, type="PicNic")
        if bon_summary.get_id() not in published_ids:
            result.append(bon_summary)
    return result


def parse_pdf_to_rewe_bon_summary(filename) -> Optional[BonSummary]:
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

        return BonSummary(sum=sum, beleg=beleg, timestamp=timestamp, type="Rewe")
    except:
        return None


def get_published_ids() -> List[str]:
    try:
        with open(os.path.join("data", "published_ids.txt"), 'r') as f:
            return [str(l).replace("\n", "") for l in f.readlines()]
    except FileNotFoundError:
        return []


def add_published_id(bon_summary: BonSummary):
    if not os.path.exists('data'):
        os.mkdir('data')
    with open(os.path.join("data", "published_ids.txt"), 'a') as f:
        f.write(bon_summary.get_id())
        f.write("\n")


def publish_bons(bons: List[BonSummary], config):
    if len(bons) > 0:
        logging.info(f"Found {len(bons)} bons")
    for bon in bons:
        logging.info(f"Pushing new bill: {bon}")
        url = 'https://cloud.jb-services.de/index.php/apps/cospend/api/projects/015f4519b2025896bbdfaf55702299cb/no-pass/bills'
        data = {
            'amount': bon.sum,
            'what': bon.type,
            'payed_for': '1,2',
            'payer': '3',
            'timestamp': (bon.timestamp - datetime.datetime(1970, 1, 1)).total_seconds(),
            'categoryid': 1,
            'paymentmodeid': 1,
            'comment': bon.type + 'Autopush - Beleg: ' + bon.beleg
        }
        logging.debug(str(data))
        result = requests.post(url, json=data)
        print(result)
        if result.status_code < 400:
            logging.debug("Add to published file")
            add_published_id(bon)
        else:
            logging.warning("Bill was not published to cospend!")
            logging.warning(f"{result.status_code}: {result.reason}")


if __name__ == '__main__':
    run()
