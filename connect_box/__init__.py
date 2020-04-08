"""A Python Client to get data from UPC Connect Boxes."""
import asyncio
import logging
from typing import Dict, List, Optional

import aiohttp
from aiohttp.hdrs import REFERER, USER_AGENT
import defusedxml.ElementTree as element_tree

from .data import (
    Device,
    DownstreamChannel,
    UpstreamChannel,
    CmStatus,
    ServiceFlow,
    Temperature,
)
from . import exceptions

_LOGGER = logging.getLogger(__name__)

HTTP_HEADER_X_REQUESTED_WITH = "X-Requested-With"

CMD_LOGIN = 15
CMD_LOGOUT = 16
CMD_DEVICES = 123
CMD_DOWNSTREAM = 10
CMD_UPSTREAM = 11
CMD_TEMPERATURE = 136
CMD_CMSTATUS = 144


class ConnectBox:
    """A class for handling the data retrieval from an UPC Connect Box."""

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
        self.ds_channels: List[DownstreamChannel] = []
        self.us_channels: List[UpstreamChannel] = []
        self.cmstatus: Optional[CmStatus] = None
        self.upstream_service_flows: List[ServiceFlow] = []
        self.downstream_service_flows: List[ServiceFlow] = []
        self.temperature: Optional[Temperature] = None

    async def async_get_devices(self):
        """Scan for new devices and return a list with found device IDs."""
        if self.token is None:
            await self.async_initialize_token()

        self.devices.clear()
        raw = await self._async_ws_function(CMD_DEVICES)

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

    async def async_get_downstream(self):
        """Get the current downstream cable modem state."""
        if self.token is None:
            await self.async_initialize_token()

        self.ds_channels.clear()
        raw = await self._async_ws_function(CMD_DOWNSTREAM)

        try:
            xml_root = element_tree.fromstring(raw)
            for downstream in xml_root.iter("downstream"):
                self.ds_channels.append(
                    DownstreamChannel(
                        int(downstream.find("freq").text),
                        int(downstream.find("pow").text),
                        downstream.find("mod").text,
                        downstream.find("chid").text,
                        float(downstream.find("RxMER").text),
                        int(downstream.find("PreRs").text),
                        int(downstream.find("PostRs").text),
                        downstream.find("IsQamLocked").text == "1",
                        downstream.find("IsFECLocked").text == "1",
                        downstream.find("IsMpegLocked").text == "1",
                    )
                )
        except (element_tree.ParseError, TypeError):
            _LOGGER.warning("Can't read downstream channels from %s", self.host)
            self.token = None
            raise exceptions.ConnectBoxNoDataAvailable() from None

    async def async_get_upstream(self):
        """Get the current upstream cable modem state."""
        if self.token is None:
            await self.async_initialize_token()

        self.us_channels.clear()
        raw = await self._async_ws_function(CMD_UPSTREAM)

        try:
            xml_root = element_tree.fromstring(raw)
            for upstream in xml_root.iter("upstream"):
                self.us_channels.append(
                    UpstreamChannel(
                        int(upstream.find("freq").text),
                        int(upstream.find("power").text),
                        upstream.find("srate").text,
                        upstream.find("usid").text,
                        upstream.find("mod").text,
                        upstream.find("ustype").text,
                        int(upstream.find("t1Timeouts").text),
                        int(upstream.find("t2Timeouts").text),
                        int(upstream.find("t3Timeouts").text),
                        int(upstream.find("t4Timeouts").text),
                        upstream.find("channeltype").text,
                        int(upstream.find("messageType").text),
                    )
                )
        except (element_tree.ParseError, TypeError):
            _LOGGER.warning("Can't read upstream channels from %s", self.host)
            self.token = None
            raise exceptions.ConnectBoxNoDataAvailable() from None

    async def async_get_cmstatus_and_service_flows(self):
        """Get various status information."""
        if self.token is None:
            await self.async_initialize_token()

        self.cmstatus = None
        self.downstream_service_flows = []
        self.upstream_service_flows = []
        raw = await self._async_ws_function(CMD_CMSTATUS)

        try:
            xml_root = element_tree.fromstring(raw)
            self.cmstatus = CmStatus(
                provisioningStatus=xml_root.find("provisioning_st").text,
                cmComment=xml_root.find("cm_comment").text,
                cmDocsisMode=xml_root.find("cm_docsis_mode").text,
                cmNetworkAccess=xml_root.find("cm_network_access").text,
                numberOfCpes=int(xml_root.find("NumberOfCpes").text),
                firmwareFilename=xml_root.find("FileName").text,
                dMaxCpes=int(xml_root.find("dMaxCpes").text),
                bpiEnable=int(xml_root.find("bpiEnable").text),
            )
            for elmt_service_flow in xml_root.iter("serviceflow"):
                service_flow = ServiceFlow(
                    id=int(elmt_service_flow.find("Sfid").text),
                    pMaxTrafficRate=int(elmt_service_flow.find("pMaxTrafficRate").text),
                    pMaxTrafficBurst=int(
                        elmt_service_flow.find("pMaxTrafficBurst").text
                    ),
                    pMinReservedRate=int(
                        elmt_service_flow.find("pMinReservedRate").text
                    ),
                    pMaxConcatBurst=int(elmt_service_flow.find("pMaxConcatBurst").text),
                    pSchedulingType=int(elmt_service_flow.find("pSchedulingType").text),
                )
                direction = int(elmt_service_flow.find("direction").text)
                if direction == 1:
                    self.downstream_service_flows.append(service_flow)
                elif direction == 2:
                    self.upstream_service_flows.append(service_flow)
                else:
                    raise element_tree.ParseError(
                        "Unknown service flow direction '{}'".format(direction)
                    )
        except (element_tree.ParseError, TypeError):
            _LOGGER.warning("Can't read cmstatus from %s", self.host)
            self.token = None
            raise exceptions.ConnectBoxNoDataAvailable() from None

    async def async_get_temperature(self):
        """Get temperature information (in degrees Celsius)."""
        if self.token is None:
            await self.async_initialize_token()

        self.temperature = None
        raw = await self._async_ws_function(CMD_TEMPERATURE)

        f_to_c = lambda f: (5.0 / 9) * (f - 32)
        try:
            xml_root = element_tree.fromstring(raw)
            self.temperature = Temperature(
                tunerTemperature=f_to_c(int(xml_root.find("TunnerTemperature").text)),
                temperature=f_to_c(int(xml_root.find("Temperature").text)),
            )
        except (element_tree.ParseError, TypeError):
            _LOGGER.warning("Can't read temperature from %s", self.host)
            self.token = None
            raise exceptions.ConnectBoxNoDataAvailable() from None

    async def async_close_session(self) -> None:
        """Logout and close session."""
        if not self.token:
            return

        await self._async_ws_function(CMD_LOGOUT)
        self.token = None

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

        except (asyncio.TimeoutError, aiohttp.ClientError) as err:
            _LOGGER.error("Can not load login page from %s: %s", self.host, err)
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
                    _LOGGER.warning("Login error with code %d", response.status)
                    self.token = None
                    raise exceptions.ConnectBoxLoginError()
                self.token = response.cookies["sessionToken"].value

        except (asyncio.TimeoutError, aiohttp.ClientError) as err:
            _LOGGER.error("Can not login to %s: %s", self.host, err)
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
                    _LOGGER.debug("Receive HTTP code %d", response.status)
                    self.token = None
                    raise exceptions.ConnectBoxError()

                # Load data, store token for next request
                self.token = response.cookies["sessionToken"].value
                return await response.text()

        except (asyncio.TimeoutError, aiohttp.ClientError) as err:
            _LOGGER.error("Error received on %s: %s", function, err)
            self.token = None

        raise exceptions.ConnectBoxConnectionError()
