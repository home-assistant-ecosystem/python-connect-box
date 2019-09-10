"""A Python Client to get data from UPC Connect Boxes."""
import asyncio
from ipaddress import IPv4Address, IPv6Address, ip_address as convert_ip
import logging
from typing import Dict, List, Optional, Union

import aiohttp
from aiohttp.hdrs import REFERER, USER_AGENT
import attr
import defusedxml.ElementTree as element_tree

from . import exceptions

_LOGGER = logging.getLogger(__name__)

HTTP_HEADER_X_REQUESTED_WITH = "X-Requested-With"

CMD_LOGIN = 15
CMD_DEVICES = 123


@attr.s
class Device:
    """A single device."""

    mac: str = attr.ib()
    hostname: str = attr.ib(cmp=False)
    ip: Union[IPv4Address, IPv6Address] = attr.ib(cmp=False, convert=convert_ip)


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
        self.devices: List[Device] = []

    async def async_get_devices(self) -> List[Device]:
        """Scan for new devices and return a list with found device IDs."""
        if self.token is None:
            await self.async_initialize_token()

        raw = await self._async_ws_function(CMD_DEVICES)
        self.devices.clear()
        try:
            xml_root = element_tree.fromstring(raw)
            mac_adresses: List[str] = [mac.text for mac in xml_root.iter("MACAddr")]
            hostnames: List[str] = [mac.text for mac in xml_root.iter("hostname")]
            ip_addresses: List[str] = [mac.text for mac in xml_root.iter("IPv4Addr")]

            for mac_address, hostname, ip_address in zip(
                mac_adresses, hostnames, ip_addresses
            ):
                self.devices.append(
                    Device(mac_address, hostname, ip_address.partition("/")[0])
                )
        except (element_tree.ParseError, TypeError):
            _LOGGER.warning("Can't read device from %s", self.host)
            self.token = None
            raise exceptions.ConnectBoxNoDataAvailable() from None

        return self.devices

    async def async_initialize_token(self) -> None:
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

        except (asyncio.TimeoutError, aiohttp.ClientError):
            _LOGGER.error("Can not load login page from %s", self.host)
            raise exceptions.ConnectBoxConnectionError()

        await self._async_initialize_token_with_password(CMD_LOGIN)

    async def _async_initialize_token_with_password(self, function: int) -> None:
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
                    raise exceptions.ConnectBoxLoginError()

                self.token = response.cookies["sessionToken"].value

        except (asyncio.TimeoutError, aiohttp.ClientError):
            _LOGGER.error("Can not login to %s", self.host)
            raise exceptions.ConnectBoxConnectionError()

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
                    raise exceptions.ConnectBoxError()

                # Load data, store token for next request
                self.token = response.cookies["sessionToken"].value
                return await response.text()

        except (asyncio.TimeoutError, aiohttp.ClientError):
            _LOGGER.error("Error on %s", function)
            self.token = None

        raise exceptions.ConnectBoxConnectionError()
