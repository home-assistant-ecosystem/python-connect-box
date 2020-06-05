"""Get the data from an UPC Connect Box."""
import asyncio
from pprint import pprint

import aiohttp
from connect_box import ConnectBox

PASSWORD = "Router_password"


async def main():
    """Sample code to retrieve the data from an UPC Connect Box."""
    async with aiohttp.ClientSession() as session:
        client = ConnectBox(session, PASSWORD)

        # Print details about the downstream channel connectivity
        await client.async_get_downstream()
        pprint(client.ds_channels)

        # Print details about the upstream channel connectivity
        await client.async_get_upstream()
        pprint(client.us_channels)

        # Print details about the connected devices
        await client.async_get_devices()
        pprint(client.devices)

        # Print IPv6 filter rules
        # (IPv6 required)
        await client.async_get_ipv6_filtering()
        pprint(client.ipv6_filters)

        # Toggle enable/disable on the first IPv6 filter rule
        new_value = await client.async_toggle_ipv6_filter(1)
        # Show the effect
        await client.async_get_ipv6_filtering()
        pprint(client.ipv6_filters)

        # Print details on general device status
        await client.async_get_cmstatus_and_service_flows()
        pprint(client.cmstatus)
        pprint(client.downstream_service_flows)
        pprint(client.upstream_service_flows)

        # Print temperature status
        await client.async_get_temperature()
        pprint(client.temperature)

        await client.async_close_session()


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
