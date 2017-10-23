# This file is part of the ISIS IBEX application.
# Copyright (C) 2017 Science & Technology Facilities Council.
# All rights reserved.
#
# This program is distributed in the hope that it will be useful.
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License v1.0 which accompanies this distribution.
# EXCEPT AS EXPRESSLY SET FORTH IN THE ECLIPSE PUBLIC LICENSE V1.0, THE PROGRAM
# AND ACCOMPANYING MATERIALS ARE PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES
# OR CONDITIONS OF ANY KIND.  See the Eclipse Public License v1.0 for more details.
#
# You should have received a copy of the Eclipse Public License v1.0
# along with this program; if not, you can obtain a copy from
# https://www.eclipse.org/org/documents/epl-v10.php or
# http://opensource.org/licenses/eclipse-1.0.php
"""
Classes getting external resources from an instrument and formating them for the info page.
"""

import requests
import json
from block_utils import (format_blocks, set_rc_values_for_blocks)
import logging

from external_webpage.web_page_parser import WebPageParser

logger = logging.getLogger('JSON_bourne')

PORT_INSTPV = 4812
PORT_BLOCKS = 4813
PORT_CONFIG = 8008


class PageReader(object):
    """
    Access of external gata sources from urls.
    """

    def __init__(self, host):
        """
        Initialize.
        Args:
            host: The host name for the instrument.
        """
        self._host = host

    def get_info(self, port, group_name):
        """
        Read block information from the archiver and populate a list of block objects with it.

        Args:
            port: the port the url is on
            group_name: the name of the group within the archiver to access.

        Returns: A converted list of block objects.

        """
        url = 'http://{host}:{port}/group?name={group_name}&format=json'.format(
            host=self._host, port=port, group_name=group_name)
        try:
            page = requests.get(url)
            return page.json()
        except Exception as e:
            logger.error("URL not found or json not understood: " + str(url))
            raise e

    def read_config(self, port):
        """
        Read the configuration from the instrument blockserver.
        Args:
            port: Port the server is on.

        Returns: The configuration as a dictionary.

        """

        # read config
        page = requests.get('http://%s:%s/' % (self._host, port))
        corrected_page = page.content\
            .replace("'", '"')\
            .replace("None", "null")\
            .replace("True", "true")\
            .replace("False", "false")
        try:
            return json.loads(corrected_page)
        except Exception as e:
            logger.error("JSON conversion failed: " + str(e))
            logger.error("JSON was: " + str(corrected_page))
            raise e


class InstrumentConfig(object):
    """
    The instrument configuration.
    """

    def __init__(self, config_json):
        """
        Initialize.
        Args:
            config_json: The json dictionary from which to create the configuration
        """
        self._config = config_json
        self.groups = self._config["groups"]
        self.name = self._config["name"]

        self.blocks = {}
        for block in self._config["blocks"]:
            self.blocks[block["name"]] = block

    def block_is_visible(self, block_name):
        """
        According to the configuration is a block visible to the user.
        Args:
            block_name: Block name to query

        Returns: True if it is visible; False otherwise
        Raises KeyError: If the block does not exist.

        """
        block = self.blocks[block_name]
        return block["visible"]


class WebPageScraper:
    """
    Collect instrument information and summarise as a dictionary.
    """

    def __init__(self, host="localhost", reader=None):
        """
        Initialize.
        Args:
            host: The host of the instrument from which to read the information.
            reader: A reader object to get external information.
        """
        if reader is None:
            self.reader = PageReader(host)
        else:
            self.reader = reader

        self.web_page_parser = WebPageParser()

    def _get_inst_pvs(self, ans, blocks_all):
        """
        Extracts and formats a list of relevant instrument PVs from all instrument PVs.

        Args:
            ans: List of blocks from the instrument archive.
            blocks_all: List of blocks from the block and dataweb archives.

        Returns: A trimmed list of instrument PVs.

        """
        wanted = {}

        required_pvs = ["RUNSTATE", "RUNNUMBER", "_RBNUMBER", "TITLE", "DISPLAY", "_USERNAME", "STARTTIME",
                        "RUNDURATION", "RUNDURATION_PD", "GOODFRAMES", "GOODFRAMES_PD", "RAWFRAMES", "RAWFRAMES_PD",
                        "PERIOD", "NUMPERIODS", "PERIODSEQ", "BEAMCURRENT", "TOTALUAMPS", "COUNTRATE", "DAEMEMORYUSED",
                        "TOTALCOUNTS", "DAETIMINGSOURCE", "MONITORCOUNTS", "MONITORSPECTRUM", "MONITORFROM", "MONITORTO",
                        "NUMTIMECHANNELS", "NUMSPECTRA"]

        try:
            set_rc_values_for_blocks(blocks_all.values(), ans)
        except Exception as e:
            logging.error("Error in setting rc values for blocks: " + str(e))

        for pv in required_pvs:
            if pv + ".VAL" in ans:
                wanted[pv] = ans[pv + ".VAL"]

        try:
            self._convert_seconds(wanted["RUNDURATION"])
        except KeyError:
            pass

        try:
            self._convert_seconds(wanted["RUNDURATION_PD"])
        except KeyError:
            pass

        return wanted

    def _convert_seconds(self, block):
        """
        Receives the value from the block and converts to hours, minutes and seconds.

        Args:
            block: the block to convert

        """
        if not block.is_connected():
            return
        old_value = block.get_value()
        seconds = int(old_value) % 60
        minutes = int(old_value) / 60
        hours = minutes / 60
        minutes %= 60

        if hours == 0 and minutes == 0:
            block.set_value(old_value + " s")
        elif hours == 0:
            block.set_value(str(minutes) + " min " + str(seconds) + " s")
        else:
            block.set_value(str(hours) + " hr " + str(minutes) + " min " + str(seconds) + " s")
        block.set_units("")

    def scrape_webpage(self):
        """
        Returns the collated information on instrument configuration, blocks and run status PVs as JSON.

        Returns: JSON of the instrument's configuration and status.

        """

        instrument_config = InstrumentConfig(self.reader.read_config(PORT_CONFIG))

        try:

            # read blocks

            blocks_log = self.web_page_parser.extract_blocks(self.reader.get_info(PORT_BLOCKS, "BLOCKS"))
            blocks_nolog = self.web_page_parser.extract_blocks(self.reader.get_info(PORT_BLOCKS, "DATAWEB"))
            blocks_all = dict(blocks_log.items() + blocks_nolog.items())

            # get block visibility from config
            for block in blocks_all:
                blocks_all[block].set_visibility(instrument_config.block_is_visible(block))

            instrument_blocks = self.web_page_parser.extract_blocks(self.reader.get_info(PORT_INSTPV, "INST"))

            inst_pvs = format_blocks(self._get_inst_pvs(instrument_blocks, blocks_all))

        except Exception as e:
            logger.error("Failed to read blocks: " + str(e))
            raise e

        blocks_all_formatted = format_blocks(blocks_all)
        groups = {}
        for group in instrument_config.groups:
            blocks = {}
            for block in group["blocks"]:
                if block in blocks_all_formatted.keys():
                    blocks[block] = blocks_all_formatted[block]
            groups[group["name"]] = blocks

        try:
            output = {
                "config_name": instrument_config.name,
                "groups": groups,
                "inst_pvs": inst_pvs}
        except Exception as e:
            logger.error("Output construction failed " + str(e))
            raise e

        return output
