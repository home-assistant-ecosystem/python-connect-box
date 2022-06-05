"""Handle Data attributes."""
from datetime import datetime
from ipaddress import IPv4Address, IPv6Address, ip_address as convert_ip
from typing import Iterable, Optional, Union

import attr


@attr.s
class Device:
    """A single device."""

    mac: str = attr.ib()
    hostname: str = attr.ib(cmp=False)
    ip: Union[IPv4Address, IPv6Address] = attr.ib(cmp=False, converter=convert_ip)
    interface: str = attr.ib()
    speed: int = attr.ib()
    interface_id: int = attr.ib()
    method: int = attr.ib()
    lease_time: str = attr.ib(
        converter=lambda lease_time: datetime.strptime(lease_time, "00:%H:%M:%S")
    )


@attr.s
class DownstreamChannel:
    """A locked downstream channel."""

    frequency: int = attr.ib()
    powerLevel: int = attr.ib()
    modulation: str = attr.ib()
    id: str = attr.ib()
    snr: float = attr.ib()
    preRs: int = attr.ib()
    postRs: int = attr.ib()
    qamLocked: bool = attr.ib()
    fecLocked: bool = attr.ib()
    mpegLocked: bool = attr.ib()


@attr.s
class UpstreamChannel:
    """A locked upstream channel."""

    frequency: int = attr.ib()
    powerLevel: int = attr.ib()
    symbolRate: str = attr.ib()
    id: str = attr.ib()
    modulation: str = attr.ib()
    type: str = attr.ib()
    t1Timeouts: int = attr.ib()
    t2Timeouts: int = attr.ib()
    t3Timeouts: int = attr.ib()
    t4Timeouts: int = attr.ib()
    channelType: str = attr.ib()
    messageType: int = attr.ib()


@attr.s
class Ipv6FilterInstance:
    """An IPv6 filter rule instance."""

    idd: int = attr.ib()
    srcAddr: Union[IPv4Address, IPv6Address] = attr.ib(converter=convert_ip)
    srcAddr: str = attr.ib()
    srcPrefix: int = attr.ib()
    dstAddr: str = attr.ib()
    dstAddr: Union[IPv4Address, IPv6Address] = attr.ib(converter=convert_ip)
    dstPrefix: int = attr.ib()
    srcPortStart: int = attr.ib()
    srcPortEnd: int = attr.ib()
    dstPortStart: int = attr.ib()
    dstPortEnd: int = attr.ib()
    protocol: int = attr.ib()
    allow: int = attr.ib()
    enabled: int = attr.ib()


@attr.s
class FiltersTimeMode:
    """Filters time setting."""

    TMode: int = attr.ib()
    XmlGeneralTime: str = attr.ib()
    XmlDailyTime: str = attr.ib()


@attr.s
class FilterStatesList:
    """A sequence of filter state instances."""

    entries: Iterable = attr.ib()


@attr.s
class FilterState:
    """A filter state instance."""

    idd: int = attr.ib()
    enabled: int = attr.ib()


@attr.s
class CmStatus:
    provisioningStatus: str = attr.ib()
    cmComment: str = attr.ib()
    cmDocsisMode: str = attr.ib()
    cmNetworkAccess: str = attr.ib()
    firmwareFilename: str = attr.ib()

    # number of IP addresses to assign via DHCP
    numberOfCpes: int = attr.ib()

    # ???
    dMaxCpes: int = attr.ib()
    bpiEnable: int = attr.ib()


@attr.s
class CmSystemInfo:
    """Cable Modem system information"""

    mac: str = attr.ib()
    serial: str = attr.ib()
    network_access: bool = attr.ib()


@attr.s
class LanStatus:
    """Information about the private side of the gateway"""

    upnp_enabled: bool = attr.ib()
    mac: str = attr.ib()
    ip4: IPv4Address = attr.ib(converter=convert_ip)
    ip6: IPv6Address = attr.ib(converter=convert_ip)


@attr.s
class WanStatus:
    """Information about the public side of the gateway"""

    mac: str = attr.ib()
    ip4: IPv4Address = attr.ib(converter=convert_ip)
    # response includes ipv6 ranges, not specific addresses


@attr.s
class GlobalSettings:
    """global settings are available regardless of auth status"""

    # 1 if logged in, 0 if logged out
    logged_in: bool = attr.ib()
    # ISP identifier
    operator_id: str = attr.ib()
    # lockout due to other user
    access_denied: bool = attr.ib()
    # If logged in, software revision
    sw_version: Optional[str] = attr.ib()


@attr.s
class ServiceFlow:
    id: int = attr.ib()
    pMaxTrafficRate: int = attr.ib()
    pMaxTrafficBurst: int = attr.ib()
    pMinReservedRate: int = attr.ib()
    pMaxConcatBurst: int = attr.ib()

    # 2 seems to be Best Effort
    pSchedulingType: int = attr.ib()


@attr.s
class Temperature:
    # temperatures in degrees Celsius
    tunerTemperature: float = attr.ib()
    temperature: float = attr.ib()

    # several other stats remain untapped here:
    # wan_ipv4_addr
    # wan_ipv6_addr, wan_ipv6_addr_entry


@attr.s
class LogEvent:
    """An entry in the eventlog_table"""

    evPrio: str = attr.ib()
    evMsg: str = attr.ib()
    evTime: str = attr.ib()
    evEpoch: int = attr.ib()
