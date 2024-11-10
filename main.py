import signal
import logging
from threading import Event

from mail2cospend.cospendconnector import publish_bongs

logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p',
                    level=logging.DEBUG)

from mail2cospend.config import load_config
from mail2cospend.mailconnector import get_imap_connection
from mail2cospend.searchadapter import all_search_adapters

exit = Event()


def run(debug=False):
    config = load_config()
    while not exit.is_set():
        imap = get_imap_connection(config)

        bons = list()
        for Adapter_cls in all_search_adapters:
            adapter = Adapter_cls(config, imap)
            this_bons = adapter.search()
            bons += this_bons
            imap.close()
        imap.shutdown()

        if not debug:
            publish_bongs(bons, config)

        exit.wait(config.interval)


def quit(signo, _frame):
    print("Interrupted by %d, shutting down" % signo)
    exit.set()


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, quit)
    signal.signal(signal.SIGINT, quit)
    signal.signal(signal.SIGHUP, quit)
    run(debug=False)
