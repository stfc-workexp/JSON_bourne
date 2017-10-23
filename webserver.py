import json
import logging
import re
import traceback
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from SocketServer import ThreadingMixIn
from logging.handlers import TimedRotatingFileHandler
from threading import Thread, active_count, RLock
from time import sleep

from external_webpage.get_webpage import WebPageScraper

logger = logging.getLogger('JSON_bourne')
handler = TimedRotatingFileHandler('log\JSON_bourne.log', when='midnight', backupCount=30)
handler.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
logger.setLevel(logging.WARNING)
logger.addHandler(handler)

HOST, PORT = '', 60000

ALL_INSTS = {"MUONFE": "NDEMUONFE"}  # Used for non NDX hosts format of {name: host}

NDX_INSTS = ["DEMO", "LARMOR", "IMAT", "IRIS", "VESUVIO", "ALF", "ZOOM", "POLARIS", "HRPD", "MERLIN", "ENGINX",
             "RIKENFE"]

for inst in NDX_INSTS:
    ALL_INSTS[inst] = "NDX" + inst

_scraped_data = {}
_scraped_data_lock = RLock()

WAIT_BETWEEN_UPDATES = 3
WAIT_BETWEEN_FAILED_UPDATES = 60
RETRIES_BETWEEN_LOGS = 60


class MyHandler(BaseHTTPRequestHandler):
    """
    Handle for web calls for Json Borne
    """

    @staticmethod
    def _get_whether_ibex_is_running_on_all_instruments(data):
        """
        Gets whether ibex is running for each instrument.
        :param data: The data scraped from the archiver webpage
        :return: A json dictionary containing the states of each instrument
        """
        active = dict()
        for key in data:
            if data[key] != "":
                active[key] = True
            else:
                active[key] = False
        return str(json.dumps(active))

    @staticmethod
    def _get_detailed_state_of_specific_instrument(instrument, data):
        """
        Gets the detailed state of a specific instrument, used to display the instrument's dataweb screen
        :param instrument: The instrument to get data for
        :param data: The data scraped from the archiver webpage
        :return: The data from the archiver webpage filtered to only contain data about the requested instrument
        """
        if instrument not in data.keys():
            raise ValueError(str(instrument) + " not known")
        if data[instrument] == "":
            raise ValueError("Instrument has become unavailable")
        try:
            return str(json.dumps(_scraped_data[instrument]))
        except Exception as err:
            raise ValueError("Unable to convert instrument data to JSON: %s" % err.message)

    def do_GET(self):
        """
        This is called by BaseHTTPRequestHandler every time a client does a GET.
        The response is written to self.wfile
        """
        try:
            # Look for the callback
            # JSONP requires a response of the format "name_of_callback(json_string)"
            # e.g. myFunction({ "a": 1, "b": 2})
            result = re.search('/?callback=(\w+)&', self.path)

            # Look for the instrument data
            instruments = re.search('&Instrument=(\w+)&', self.path)

            if result is None or instruments is None:
                raise ValueError("No instrument specified")

            if len(result.groups()) != 1 or len(instruments.groups()) != 1:
                raise ValueError("No instrument specified")

            callback = result.groups()[0]
            inst_uppercase = instruments.groups()[0].upper()

            # Warn level so as to avoid many log messages that come from other modules
            logger.warn("Connected to from " + str(self.client_address) + " looking at " + str(inst_uppercase))

            with _scraped_data_lock:
                if inst_uppercase == "ALL":
                    ans = self._get_whether_ibex_is_running_on_all_instruments(_scraped_data)
                else:
                    ans = self._get_detailed_state_of_specific_instrument(inst_uppercase, _scraped_data)

            response = "{}({})".format(callback, ans)

            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(response)
        except ValueError as e:
            logger.error(e)
            logger.warn("Return 400 because of error!")
            self.send_response(400)
        except Exception as e:
            self.send_response(404)
            logger.error(e)

    def log_message(self, format, *args):
        """ By overriding this method and doing nothing we disable writing to console
         for every client request. Remove this to re-enable """
        return


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""


class WebScraper(Thread):
    """
    Information for instruments based on external source.
    """
    _running = True
    _previously_failed = False
    _tries_since_logged = 0

    def wait(self, seconds):
        """
        Wait for a number of seconds but in short waits so can stop thread more quickly
        Args:
            seconds: number of seconds to wait

        Returns:

        """
        for i in range(seconds):
            if not self._running:
                return
            sleep(1)

    def __init__(self, name, host):
        """
        Initialize.
        Args:
            name: Name of instrument.
            host: Host for the instrument.
        """
        super(WebScraper, self).__init__()
        self._host = host
        self._name = name

    def run(self):
        """
        Function to run continuously to update the scraped data.
        Returns:

        """
        global _scraped_data
        web_page_scraper = WebPageScraper(self._host)
        while self._running:
            try:
                self._tries_since_logged += 1
                temp_data = web_page_scraper.scrape_webpage()
                with _scraped_data_lock:
                    _scraped_data[self._name] = temp_data
                if self._previously_failed:
                    logger.error("Reconnected with " + str(self._name))
                self._previously_failed = False
                self.wait(WAIT_BETWEEN_UPDATES)
            except Exception as e:
                if not self._previously_failed or self._tries_since_logged >= RETRIES_BETWEEN_LOGS:
                    logger.error("Failed to get data from instrument: {0} at {1} error was: {2}{3}".format(
                        self._name, self._host, e, " - Stack (1 line) {stack}:".format(stack=traceback.format_exc())))
                    self._previously_failed = True
                    self._tries_since_logged = 0
                with _scraped_data_lock:
                    _scraped_data[self._name] = ""
                self.wait(WAIT_BETWEEN_FAILED_UPDATES)

if __name__ == '__main__':
    web_scrapers = []
    for inst_name, inst_host in ALL_INSTS.items():
        web_scraper = WebScraper(inst_name, inst_host)
        web_scraper.start()
        web_scrapers.append(web_scraper)

    server = ThreadedHTTPServer(('', PORT), MyHandler)

    try:
        while True:
            server.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down")
        for w in web_scrapers:
            w._running = False
    while active_count() > 1:
        for w in web_scrapers:
            w.join()
