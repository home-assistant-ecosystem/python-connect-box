"""A Python Client to get data from UPC Connect Boxes."""
import asyncio
import logging

import aiohttp
import async_timeout
from aiohttp.hdrs import REFERER, USER_AGENT

from . import exceptions

_LOGGER = logging.getLogger(__name__)

HTTP_HEADER_X_REQUESTED_WITH = 'X-Requested-With'

CMD_DEVICES = 123


class ConnectBox(object):
    """A class for handling the data retrieval from an UPC Connect Box ."""

    def __init__(self, loop, session, host='192.168.0.1'):
        """Initialize the connection."""
        self._loop = loop
        self._session = session
        self.token = None
        self.host = host
        self.headers = {
            HTTP_HEADER_X_REQUESTED_WITH: 'XMLHttpRequest',
            REFERER: "http://{}/index.html".format(self.host),
            USER_AGENT: ("Mozilla/5.0 (Windows NT 10.0; WOW64) "
                         "AppleWebKit/537.36 (KHTML, like Gecko) "
                         "Chrome/47.0.2526.106 Safari/537.36"),
        }
        self.data = None

    async def async_get_devices(self):
        """Scan for new devices and return a list with found device IDs."""
        import defusedxml.ElementTree as ET

        if self.token is None:
            token_initialized = await self.async_initialize_token()
            if not token_initialized:
                _LOGGER.error("Not connected to %s", self.host)
                return []

        raw = await self._async_ws_function(CMD_DEVICES)

        try:
            xml_root = ET.fromstring(raw)
            mac_adresses = [mac.text for mac in xml_root.iter('MACAddr')]
            hostnames = [mac.text for mac in xml_root.iter('hostname')]
            ip_addresses = [mac.text for mac in xml_root.iter('IPv4Addr')]

            device_list = []
            for mac_address, hostname, ip_address in zip(
                    mac_adresses, hostnames, ip_addresses):
                device_list.append({mac_address: {
                    'hostname': hostname,
                    'ip_address': ip_address,
                }})
            self.data = {'devices': device_list}
        except (ET.ParseError, TypeError):
            _LOGGER.warning("Can't read device from %s", self.host)
            self.token = None
            return []

    async def async_initialize_token(self):
        """Get the token first."""
        try:
            # Get first the token
            with async_timeout.timeout(10, loop=self._loop):
                response = await self._session.get(
                    "http://{}/common_page/login.html".format(self.host),
                    headers=self.headers)

                await response.text()

            self.token = response.cookies['sessionToken'].value

            return True

        except (asyncio.TimeoutError, aiohttp.ClientError):
            _LOGGER.error("Can not load login page from %s", self.host)
            return False

    async def _async_ws_function(self, function):
        """Execute a command on UPC firmware webservice."""
        try:
            with async_timeout.timeout(10, loop=self._loop):
                # The 'token' parameter has to be first, and 'fun' second
                # or the UPC firmware will return an error
                response = await self._session.post(
                    "http://{}/xml/getter.xml".format(self.host),
                    data="token={}&fun={}".format(self.token, function),
                    headers=self.headers, allow_redirects=False)

                # If there is an error
                if response.status != 200:
                    _LOGGER.warning("Receive http code %d", response.status)
                    self.token = None
                    return

                # Load data, store token for next request
                self.token = response.cookies['sessionToken'].value
                return await response.text()

        except (asyncio.TimeoutError, aiohttp.ClientError):
            _LOGGER.error("Error on %s", function)
            self.token = None
