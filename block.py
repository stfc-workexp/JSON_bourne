# This file is part of the ISIS IBEX application.
# Copyright (C) 2012-2016 Science & Technology Facilities Council.
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
Classes for Blocks
"""


# Temporary fix to prevent RC values from being returned from the server
# while there is still a problem with getting rc values from the archiver.
# Once that problem has been solved then this flag and it's usages can 
# be removed. See issue #2446
RETURN_RC_VALUES = False


class Block:
    """
    Class holding Block details. Used for displaying in dataweb
    """

    # Status when the block is connected
    CONNECTED = "Connected"

    # Status hen the block is disconnected
    DISCONNECTED = "Disconnected"

    def __init__(self, name, status, value, alarm, visibility, units=""):
        """
        Standard constructor.

        Args:
            name: the name of the block
            status: the status of the block (e.g disconnected)
            value: the current block value
            alarm: the alarm status
            units: units associated with the value
        """
        self.name = name
        self.status = status
        self.value = value
        self.alarm = alarm
        self.visibility = visibility
        self.low = None
        self.high = None
        self.inrange = None
        self.enabled = "NO"
        self.units = units

    def get_name(self):
        """ Returns the block status. """
        return self.name

    def set_name(self, name):
        """ Sets the block status. """
        self.status = name

    def get_status(self):
        """ Returns the block status. """
        return self.status

    def set_status(self, status):
        """ Sets the block status. """
        self.status = status

    def get_value(self):
        """ Returns the block value. """
        return self.value

    def set_value(self, value):
        """ Sets the block value. """
        self.value = value

    def get_units(self):
        """ Returns the units for the block. """
        return self.units

    def set_units(self, units):
        """ Returns the units for the block. """
        self.units = units

    def get_alarm(self):
        """ Returns the block alarm state. """
        return self.alarm

    def set_alarm(self, alarm):
        """ Sets the block alarm state. """
        self.alarm = alarm

    def get_visibility(self):
        """ Returns the block's visibility """
        return self.visibility

    def set_visibility(self, visibility):
        """ Sets the block's visibility. """
        self.visibility = visibility

    def get_rc_low(self):
        """ Returns the block's low value. """
        return self.low

    def set_rc_low(self, value):
        """ Sets the block's low value. """
        self.low = value

    def get_rc_high(self):
        """ Returns the block's high value. """
        return self.high

    def set_rc_high(self, value):
        """ Sets the block's high value. """
        self.high = value

    def get_rc_inrange(self):
        """ Returns the block's inrange status. """
        return self.inrange

    def set_rc_inrange(self, value):
        """ Sets the block's inrange status. """
        self.inrange = value

    def get_rc_enabled(self):
        """ Returns the block's enabled status. """
        return self.enabled

    def set_rc_enabled(self, value):
        """ Sets the block's enabled status. """
        self.enabled = value

    def is_connected(self):
        """
        :return Whether this block is connected
        """
        return self.status == Block.CONNECTED

    def get_description(self):
        """ Returns the full description of this BoolStr object. """
        if self.units == "":
            formatted_value = self.value
        else:
            formatted_value = "{value} {units}".format(value=self.value, units=self.units)
        ans = {
            "status": self.status,
            "value": formatted_value,
            "alarm": self.alarm,
            "visibility": self.visibility}

        if RETURN_RC_VALUES:
            # add rc values if they're set
            if self.low is not None:
                ans["rc_low"] = self.low

            if self.high is not None:
                ans["rc_high"] = self.high

            if self.inrange is not None:
                ans["rc_inrange"] = self.inrange

            ans["rc_enabled"] = self.enabled

        return ans

    def __str__(self):
        return self.get_description().__str__()
