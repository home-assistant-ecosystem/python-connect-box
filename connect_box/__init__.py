"""A Python Client to get data from UPC Connect Boxes."""
import asyncio
import logging
from typing import Any, Dict, List, Optional

import aiohttp
from aiohttp.hdrs import REFERER, USER_AGENT

from . import exceptions

_LOGGER = logging.getLogger(__name__)

HTTP_HEADER_X_REQUESTED_WITH = "X-Requested-With"

CMD_LOGIN = 15
CMD_DEVICES = 123


class ConnectBox:
    """A class for handling the data retrieval from an UPC Connect Box ."""

    def __init__(
        self, session: aiohttp.ClientSession, password: str, host: str = "192.168.0.1"
    ):
        """Initialize the connection."""
        self._session: aiohttp.ClientSession = session
        self.token: Optional[str] = None
        self.host: str = host
        self.password: str = password
        self.headers: Dict[str, str] = {
            HTTP_HEADER_X_REQUESTED_WITH: "XMLHttpRequest",
            REFERER: f"http://{self.host}/index.html",
            USER_AGENT: (
                "Mozilla/5.0 (Windows NT 10.0; WOW64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/47.0.2526.106 Safari/537.36"
            ),
        }
        self.data: Optional[Dict[str, Any]] = None

    async def async_get_devices(self) -> List[Dict[str, str]]:
        """Scan for new devices and return a list with found device IDs."""
        import defusedxml.ElementTree as element_tree

        if self.token is None:
            token_initialized = await self.async_initialize_token()
            if not token_initialized:
                _LOGGER.error("Not connected to %s", self.host)
                return []

        raw = await self._async_ws_function(CMD_DEVICES)

        try:
            xml_root = element_tree.fromstring(raw)
            mac_adresses = [mac.text for mac in xml_root.iter("MACAddr")]
            hostnames = [mac.text for mac in xml_root.iter("hostname")]
            ip_addresses = [mac.text for mac in xml_root.iter("IPv4Addr")]

            device_list = []
            for mac_address, hostname, ip_address in zip(
                mac_adresses, hostnames, ip_addresses
            ):
                device_list.append(
                    {mac_address: {"hostname": hostname, "ip_address": ip_address}}
                )
            self.data = {"devices": device_list}
        except (element_tree.ParseError, TypeError):
            _LOGGER.warning("Can't read device from %s", self.host)
            self.token = None
            return []

    async def async_initialize_token(self) -> bool:
        """Get the token first."""
        try:
            # Get first the token
            async with self._session.get(
                f"http://{self.host}/common_page/login.html",
                headers=self.headers,
                timeout=10,
            ) as response:

                await response.text()

            self.token = response.cookies["sessionToken"].value
            if self.token is None:
                return False

            return await self._async_initialize_token_with_password(CMD_LOGIN)

        except (asyncio.TimeoutError, aiohttp.ClientError):
            _LOGGER.error("Can not load login page from %s", self.host)
            return False

    async def _async_initialize_token_with_password(self, function: int) -> bool:
        """Get token with password."""
        try:
            async with await self._session.post(
                f"http://{self.host}/xml/setter.xml",
                data=f"token={self.token}&fun={function}&Username=NULL&Password={self.password}",
                headers=self.headers,
                allow_redirects=False,
                timeout=10,
            ) as response:

                await response.text()

            if response.status != 200:
                _LOGGER.warning("Receive http code %d", response.status)
                self.token = None
                return False

            self.token = response.cookies["sessionToken"].value
            return True

        except (asyncio.TimeoutError, aiohttp.ClientError):
            _LOGGER.error("Can not login to %s", self.host)
            return False

    async def _async_ws_function(self, function: int) -> Optional[str]:
        """Execute a command on UPC firmware webservice."""
        try:
            # The 'token' parameter has to be first, and 'fun' second
            # or the UPC firmware will return an error
            async with await self._session.post(
                f"http://{self.host}/xml/getter.xml",
                data=f"token={self.token}&fun={function}",
                headers=self.headers,
                allow_redirects=False,
                timeout=10,
            ) as response:

                # If there is an error
                if response.status != 200:
                    _LOGGER.warning("Receive http code %d", response.status)
                    self.token = None
                    return

                # Load data, store token for next request
                self.token = response.cookies["sessionToken"].value
                return await response.text()

        except (asyncio.TimeoutError, aiohttp.ClientError):
            _LOGGER.error("Error on %s", function)
            self.token = None

        return None
