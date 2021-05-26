"""A Python Client to get data from UPC Connect Boxes."""
import asyncio
import logging
from typing import Dict, List, Optional
from collections import OrderedDict

import attr
import aiohttp
from aiohttp.hdrs import REFERER, USER_AGENT
import defusedxml.ElementTree as element_tree

from .parsers import _parse_general_time, _parse_daily_time

from .data import (
    Device,
    DownstreamChannel,
    UpstreamChannel,
    CmStatus,
    ServiceFlow,
    Temperature,
    Ipv6FilterInstance, 
    FilterState, 
    FilterStatesList, 
    FiltersTimeMode,
    LogEvent,
)

from . import exceptions


_LOGGER = logging.getLogger(__name__)

HTTP_HEADER_X_REQUESTED_WITH = "X-Requested-With"

CMD_LOGIN = 15
CMD_LOGOUT = 16
CMD_DEVICES = 123
CMD_DOWNSTREAM = 10
CMD_UPSTREAM = 11
CMD_GET_IPV6_FILTER_RULE = 111
CMD_SET_IPV6_FILTER_RULE = 112
CMD_TEMPERATURE = 136
CMD_CMSTATUS = 144
CMD_EVENTLOG = 13


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
        self.ipv6_filters: List[Ipv6FilterInstance] = []
        self._ipv6_filters_time: FiltersTimeMode = None
        self.cmstatus: Optional[CmStatus] = None
        self.upstream_service_flows: List[ServiceFlow] = []
        self.downstream_service_flows: List[ServiceFlow] = []
        self.temperature: Optional[Temperature] = None

    async def async_get_devices(self):
        """Scan for new devices and return a list with found device IDs."""
        if self.token is None:
            await self.async_initialize_token()

        self.devices.clear()
        raw = await self._async_ws_get_function(CMD_DEVICES)

        try:
            xml_root = element_tree.fromstring(raw)
            mac_adresses: List[str] = [mac.text for mac in xml_root.iter("MACAddr")]
            hostnames: List[str] = [mac.text for mac in xml_root.iter("hostname")]
            ip_addresses: List[str] = [mac.text for mac in xml_root.iter("IPv4Addr")]
            interfaces: List[str] = [mac.text for mac in xml_root.iter("interface")]
            speeds: List[str] = [mac.text for mac in xml_root.iter("speed")]
            interface_ids: List[str] = [
                mac.text for mac in xml_root.iter("interfaceid")
            ]
            methods: List[str] = [mac.text for mac in xml_root.iter("method")]
            lease_times: List[str] = [mac.text for mac in xml_root.iter("leaseTime")]

            for (
                mac_address,
                hostname,
                ip_address,
                interface,
                speed,
                interface_id,
                method,
                lease_time,
            ) in zip(
                mac_adresses,
                hostnames,
                ip_addresses,
                interfaces,
                speeds,
                interface_ids,
                methods,
                lease_times,
            ):
                self.devices.append(
                    Device(
                        mac_address,
                        hostname,
                        ip_address.partition("/")[0],
                        interface,
                        speed,
                        interface_id,
                        method,
                        lease_time,
                    )
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
        raw = await self._async_ws_get_function(CMD_DOWNSTREAM)

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
        raw = await self._async_ws_get_function(CMD_UPSTREAM)

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

    async def async_get_ipv6_filtering(self) -> None:
        """Get the current ipv6 filter (and filters time) rules."""
        if self.token is None:
            await self.async_initialize_token()

        self.ipv6_filters.clear()
        self._ipv6_filters_time = None
        raw = await self._async_ws_get_function(CMD_GET_IPV6_FILTER_RULE)

        try:
            xml_root = element_tree.fromstring(raw)
            for instance in xml_root.iter("instance"):
                self.ipv6_filters.append(
                    Ipv6FilterInstance(
                        int(instance.find("idd").text),
                        instance.find("src_addr").text,
                        int(instance.find("src_prefix").text),
                        instance.find("dst_addr").text,
                        int(instance.find("dst_prefix").text),
                        int(instance.find("src_sport").text),
                        int(instance.find("src_eport").text),
                        int(instance.find("dst_sport").text),
                        int(instance.find("dst_eport").text),
                        int(instance.find("protocol").text),
                        int(instance.find("allow").text),
                        int(instance.find("enabled").text),
                    )
                )

            self._ipv6_filters_time = FiltersTimeMode(
                int(xml_root.find("time_mode").text),
                _parse_general_time(xml_root),
                _parse_daily_time(xml_root)
            )

        except (element_tree.ParseError, TypeError):
            _LOGGER.warning("Can't read IPv6 filter rules from %s", self.host)
            self.token = None
            raise exceptions.ConnectBoxNoDataAvailable() from None

    async def _async_get_ipv6_filter_states(self) -> FilterStatesList:
        """Get enable/disable states of IPv6 filter instances"""
        await self.async_get_ipv6_filtering()
        return FilterStatesList(list(FilterState(filter_instance.idd, filter_instance.enabled) for filter_instance in self.ipv6_filters))

    async def _async_update_ipv6_filter_states(self, filter_states: FilterStatesList):
        """Update enable/disable states of IPv6 filters while not affecting any other setting"""
        if self.token is None:
            await self.async_initialize_token()

        val_enabled = '*'.join([str(fs.enabled) for fs in filter_states.entries])
        val_del = '*'.join(['0' for fs in filter_states.entries])
        val_idd = '*'.join([str(fs.idd) for fs in filter_states.entries])

        params = OrderedDict()
        params['act'] = 1
        params['dir'] = 0
        params['enabled'] = val_enabled
        params['allow_traffic'] = ''
        params['protocol'] = ''
        params['src_addr'] = ''
        params['src_prefix'] = ''
        params['dst_addr'] = ''
        params['dst_prefix'] = ''
        params['ssport'] = ''
        params['seport'] = ''
        params['dsport'] = ''
        params['deport'] = ''
        params['del'] = val_del
        params['idd'] = val_idd
        params['sIpRange'] = ''
        params['dsIpRange'] = ''
        params['PortRange'] = ''
        params['TMode'] = self._ipv6_filters_time.TMode
        if self._ipv6_filters_time.TMode == 1:
            params['TRule'] = self._ipv6_filters_time.XmlGeneralTime
        elif self._ipv6_filters_time.TMode == 2:
            params['TRule'] = self._ipv6_filters_time.XmlDailyTime
        else:
            params['TRule'] = 0

        await self._async_ws_set_function(CMD_SET_IPV6_FILTER_RULE, params)

    async def async_toggle_ipv6_filter(self, idd: int) -> Optional[bool]:
        """Toggle enable/disable of the filter with a given idd."""
        states = await self._async_get_ipv6_filter_states()
        new_value = None

        for st in states.entries:
            if st.idd == idd:
                st.enabled = int(not bool(st.enabled))
                new_value = bool(st.enabled)
                break
        if new_value is not None:
            await self._async_update_ipv6_filter_states(states)
            return new_value

        _LOGGER.warning("Filter %d not found", idd)
        return None

    async def async_get_cmstatus_and_service_flows(self):
        """Get various status information."""
        if self.token is None:
            await self.async_initialize_token()

        self.cmstatus = None
        self.downstream_service_flows = []
        self.upstream_service_flows = []
        raw = await self._async_ws_get_function(CMD_CMSTATUS)

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
        raw = await self._async_ws_get_function(CMD_TEMPERATURE)

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

    async def async_get_eventlog(self):
        """Get network-related eventlog data."""
        if self.token is None:
            await self.async_initialize_token()

        self.eventlog = []
        raw = await self._async_ws_get_function(CMD_EVENTLOG)

        try:
            xml_root = element_tree.fromstring(raw)
            for elmt_log_event in xml_root.iter("eventlog"):
                log_event = LogEvent(
                elmt_log_event.find("prior").text,
                elmt_log_event.find("text").text,
                elmt_log_event.find("time").text,
                int(elmt_log_event.find("t").text),
                )
                self.eventlog.append(log_event)
        except (element_tree.ParseError, TypeError):
            _LOGGER.warning("Can't read eventlog from %s", self.host)
            self.token = None
            raise exceptions.ConnectBoxNoDataAvailable() from None
        self.eventlog.sort(key=(lambda e: e.evEpoch))

    async def async_close_session(self) -> None:
        """Logout and close session."""
        if not self.token:
            return

        await self._async_ws_set_function(CMD_LOGOUT, {})
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

    async def _async_ws_get_function(self, function: int) -> Optional[str]:
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

    async def _async_ws_set_function(self, function: int, params: dict) -> Optional[bool]:
        """Execute a set command on UPC firmware webservice.

        Args:
            function(int): set function id
            params(dict): key/value pairs to be passed to the function
        """
        try:
            # The 'token' parameter has to be first, and 'fun' second
            # or the UPC firmware will return an error
            params_str = ''.join([f'&{key}={value}' for (key, value) in params.items()])

            async with await self._session.post(
                f"http://{self.host}/xml/setter.xml",
                data=f"token={self.token}&fun={function}{params_str}",
                #data=params,
                headers=self.headers,
                allow_redirects=False,
                timeout=10,
            ) as response:

                # If there is an error
                if response.status != 200:
                    _LOGGER.debug("Receive HTTP code %d", response.status)
                    self.token = None
                    print(response.status)
                    print(response.content)
                    raise exceptions.ConnectBoxError()

                # Load data, store token for next request
                self.token = response.cookies["sessionToken"].value
                await response.text()
                return True

        except (asyncio.TimeoutError, aiohttp.ClientError) as err:
            _LOGGER.error("Error received on %s: %s", function, err)
            self.token = None

        raise exceptions.ConnectBoxConnectionError()
