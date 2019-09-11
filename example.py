"""Get the data from an UPC Connect Box."""
import asyncio

import aiohttp

from connect_box import ConnectBox


async def main():
    """Sample code to retrieve the data from an UPC Connect Box."""
    async with aiohttp.ClientSession() as session:
        client = ConnectBox(session, "password")

        # Print details about the connected devices
        await client.async_get_devices()
        print(client.devices)

        await client.async_close_session()


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
