"""Handle Data attributes."""
from ipaddress import IPv4Address, IPv6Address, ip_address as convert_ip
from typing import Union

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
