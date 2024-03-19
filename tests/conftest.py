from contextlib import contextmanager
import re

import pytest
import aiohttp
from connect_box import ConnectBox
import os
from vcr.record_mode import RecordMode


@pytest.fixture(scope="module")
def vcr_config():
    # Hide sensitive values in cassettes.
    def before_record_request_cb(request):
        request.uri = re.sub(r"Password=\d+", "Password=[PASSWORD]", request.uri)

        if request.body:
            text_body = request.body.decode()
            text_body = re.sub(r"token=\d+", "token=[SESSION_TOKEN]", text_body)
            text_body = re.sub(r"Password=\d+", "Password=[PASSWORD]", text_body)
            request.body = text_body.encode()
        return request

    def before_record_response_cb(response):
        response["headers"]["Set-Cookie"] = [
            re.sub(r"sessionToken=\d+", "sessionToken=[SESSION_TOKEN]", header_value)
            for header_value in response["headers"]["Set-Cookie"]
        ]

        return response

    return {
        "before_record_request": before_record_request_cb,
        "before_record_response": before_record_response_cb,
    }


@pytest.fixture
def vcr_recorder(vcr, vcr_cassette_name):
    @contextmanager
    def vcr_recorder_wrapper(**kwargs):
        # VCR is initialized with the configuration from vcr_config (see above)
        with vcr.use_cassette(vcr_cassette_name, **kwargs) as cassette:
            yield cassette

    return vcr_recorder_wrapper


@pytest.fixture
async def device_password(vcr):
    device_password = os.environ.get("DEVICE_PASSWORD")
    if vcr.record_mode != RecordMode.NONE and device_password is None:
        pytest.fail(
            "To create VCR cassettes, you need to set the DEVICE_PASSWORD environment variable. "
            "You can also run tests with the --vcr-record=none flag to use only existings cassettes."
        )
    return device_password or "12345"


@pytest.fixture
@pytest.mark.asyncio
async def client(vcr, device_password):
    async with aiohttp.ClientSession() as session:
        client = ConnectBox(session, device_password)

        # If VCR recording is active, initialize client with real token.
        # Thanks to this, this request will not be repeated in each cassette.
        # Otherwise, use a fixed value.
        if vcr.record_mode != RecordMode.NONE:
            await client.async_initialize_token()
        else:
            client.token = "[SESSION_TOKEN]"

        yield client
