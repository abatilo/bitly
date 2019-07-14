import asyncio
from collections import namedtuple

import pytest
from aioresponses import aioresponses

from bitly.handlers import fetch_averaged_metrics_per_country


Request = namedtuple("Request", "token")


@pytest.fixture
def req():
    return Request("Bearer some_token_would_go_here")


@pytest.fixture
def headers():
    return {"Authorization": "Bearer some_token_would_go_here"}


@pytest.mark.asyncio
async def test_happy_path(req, headers):
    fetch_default_group_id_success = {"default_group_guid": "default_guid"}
    fetch_bitlink_ids_success = {
        "links": [{"id": "aaronbatilo.dev"}],
        "pagination": {"total": 1, "size": 1},
    }
    fetch_clicks_per_country_success = {
        "metrics": [
            {
            "value": "US",
            "clicks": 1
            }
        ]
    }


    with aioresponses() as mock:
        mock.get(
            "https://api-ssl.bitly.com/v4/user",
            headers=headers,
            payload=fetch_default_group_id_success,
        )
        mock.get(
            "https://api-ssl.bitly.com/v4/groups/default_guid/bitlinks",
            headers=headers,
            payload=fetch_bitlink_ids_success,
        )
        mock.get(
            "https://api-ssl.bitly.com/v4/bitlinks/aaronbatilo.dev/countries?unit=day&units=30",
            headers=headers,
            payload=fetch_clicks_per_country_success,
        )

        await fetch_averaged_metrics_per_country(req)
