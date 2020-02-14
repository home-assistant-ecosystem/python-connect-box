"""Handle Data attributes."""
from ipaddress import IPv4Address, IPv6Address, ip_address as convert_ip
from typing import Union, Iterable

import attr


@attr.s
class Device:
    """A single device."""

    mac: str = attr.ib()
    hostname: str = attr.ib(cmp=False)
    ip: Union[IPv4Address, IPv6Address] = attr.ib(cmp=False, converter=convert_ip)


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
