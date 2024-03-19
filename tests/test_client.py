from contextlib import contextmanager
import aiohttp

import pytest
from connect_box import ConnectBox


@pytest.mark.asyncio
async def test_async_initialize_token(client, vcr_recorder):
    with vcr_recorder():
        await client.async_initialize_token()

    assert client.token == "[SESSION_TOKEN]"


@pytest.mark.asyncio
async def test_async_get_devices(client, vcr_recorder, snapshot):
    with vcr_recorder():
        await client.async_get_devices()

    assert client.devices == snapshot


@pytest.mark.asyncio
async def test_async_get_downstream(client, vcr_recorder, snapshot):
    with vcr_recorder():
        await client.async_get_downstream()

    assert client.ds_channels == snapshot


@pytest.mark.asyncio
async def test_async_get_devices(client, vcr_recorder, snapshot):
    with vcr_recorder():
        await client.async_get_devices()

    assert client.devices == snapshot


@pytest.mark.asyncio
async def test_async_get_ipv6_filtering(client, vcr_recorder, snapshot):
    with vcr_recorder():
        await client.async_get_ipv6_filtering()

    assert client.ipv6_filters == snapshot


@pytest.mark.asyncio
async def test_async_async_toggle_ipv6_filter(client, vcr_recorder, snapshot):
    with vcr_recorder():
        result = await client.async_toggle_ipv6_filter(1)

    assert result == snapshot


@pytest.mark.asyncio
async def test_async_get_lanstatus(client, vcr_recorder, snapshot):
    with vcr_recorder():
        await client.async_get_lanstatus()

    assert client.lanstatus == snapshot


@pytest.mark.asyncio
async def test_async_get_wanstatus(client, vcr_recorder, snapshot):
    with vcr_recorder():
        await client.async_get_wanstatus()

    assert client.wanstatus == snapshot


@pytest.mark.asyncio
async def test_async_get_wanstatus(client, vcr_recorder, snapshot):
    with vcr_recorder():
        await client.async_get_cm_system_info()

    assert client.cm_systeminfo == snapshot


@pytest.mark.asyncio
async def test_async_get_wanstatus(client, vcr_recorder, snapshot):
    with vcr_recorder():
        await client.async_get_cmstatus_and_service_flows()

    assert client.cmstatus == snapshot
    assert client.downstream_service_flows == snapshot
    assert client.upstream_service_flows == snapshot


@pytest.mark.asyncio
async def test_async_get_temperature(client, vcr_recorder, snapshot):
    with vcr_recorder():
        await client.async_get_temperature()

    assert client.temperature == snapshot


@pytest.mark.asyncio
async def test_async_get_eventlog(client, vcr_recorder, snapshot):
    with vcr_recorder():
        await client.async_get_eventlog()

    assert client.eventlog == snapshot


@pytest.mark.asyncio
async def test_async_reboot_device(client, vcr_recorder, snapshot):
    with vcr_recorder():
        await client.async_reboot_device()

    assert client.token == None


@pytest.mark.asyncio
async def test_async_close_session(client, vcr_recorder):
    with vcr_recorder():
        await client.async_close_session()


@pytest.mark.asyncio
async def test_async_get_global_settings(client, vcr_recorder, snapshot):
    with vcr_recorder():
        await client.async_get_global_settings()

    assert client.global_settings == snapshot


@pytest.mark.asyncio
async def test_async_get_global_settings(client, vcr_recorder, snapshot):
    with vcr_recorder():
        await client.async_get_global_settings()

    assert client.global_settings == snapshot
