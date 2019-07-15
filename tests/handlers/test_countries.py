import asyncio
import json
from http import HTTPStatus
from collections import namedtuple

import pytest
from aioresponses import aioresponses
from sanic.exceptions import ServerError

from bitly.handlers import fetch_averaged_metrics_per_country


Request = namedtuple("Request", "token")


@pytest.fixture
def req():
    return Request("Bearer some_token_would_go_here")


@pytest.fixture
def headers():
    return {"Authorization": "Bearer some_token_would_go_here"}


@pytest.mark.asyncio
async def test_basic_happy_path(req, headers):
    fetch_default_group_id_success = {"default_group_guid": "default_guid"}
    fetch_bitlink_ids_success = {
        "links": [{"id": "aaronbatilo.dev"}],
        "pagination": {"total": 2, "size": 1},
    }
    fetch_bitlink_ids_second_success = {
        "links": [{"id": "aaronbatilo.dev2"}],
        "pagination": {"total": 2, "size": 1},
    }
    fetch_clicks_per_country_success = {"metrics": [{"value": "US", "clicks": 1}]}

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
            "https://api-ssl.bitly.com/v4/groups/default_guid/bitlinks?page=2",
            headers=headers,
            payload=fetch_bitlink_ids_second_success,
        )
        mock.get(
            "https://api-ssl.bitly.com/v4/bitlinks/aaronbatilo.dev/countries?unit=day&units=30",
            headers=headers,
            payload=fetch_clicks_per_country_success,
        )
        mock.get(
            "https://api-ssl.bitly.com/v4/bitlinks/aaronbatilo.dev2/countries?unit=day&units=30",
            headers=headers,
            payload=fetch_clicks_per_country_success,
        )

        expected = {
            "metrics": {"type": "clicks", "US": 0.0666666667},
            "unit": "day",
            "units": 30,
        }
        actual = json.loads((await fetch_averaged_metrics_per_country(req)).body)
        assert expected == actual


@pytest.mark.asyncio
async def test_fetch_default_group_id_fails(req, headers):
    with aioresponses() as mock:
        mock.get(
            "https://api-ssl.bitly.com/v4/user",
            headers=headers,
            status=HTTPStatus.INTERNAL_SERVER_ERROR,
        )

        with pytest.raises(
            ServerError, match="There was a problem retrieving the group id"
        ):
            await fetch_averaged_metrics_per_country(req)


@pytest.mark.asyncio
async def test_fetch_bitlink_ids_initial_request_fails(req, headers):
    fetch_default_group_id_success = {"default_group_guid": "default_guid"}

    with aioresponses() as mock:
        mock.get(
            "https://api-ssl.bitly.com/v4/user",
            headers=headers,
            payload=fetch_default_group_id_success,
        )
        mock.get(
            "https://api-ssl.bitly.com/v4/groups/default_guid/bitlinks",
            headers=headers,
            status=HTTPStatus.INTERNAL_SERVER_ERROR,
        )

        with pytest.raises(
            ServerError,
            match="There was a problem getting the bitlink" " ids for your group",
        ):
            await fetch_averaged_metrics_per_country(req)


@pytest.mark.asyncio
async def test_fetch_bitlink_ids_secondary_request_fails(req, headers):
    fetch_default_group_id_success = {"default_group_guid": "default_guid"}
    fetch_bitlink_ids_success = {
        "links": [{"id": "aaronbatilo.dev"}],
        "pagination": {"total": 2, "size": 1},
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
            "https://api-ssl.bitly.com/v4/groups/default_guid/bitlinks?page=2",
            headers=headers,
            status=HTTPStatus.INTERNAL_SERVER_ERROR,
        )

        with pytest.raises(
            ServerError,
            match="There was a problem getting the bitlink ids for your group",
        ):
            await fetch_averaged_metrics_per_country(req)


@pytest.mark.asyncio
async def test_fetch_clicks_per_country_fails(req, headers):
    fetch_default_group_id_success = {"default_group_guid": "default_guid"}
    fetch_bitlink_ids_success = {
        "links": [{"id": "aaronbatilo.dev"}],
        "pagination": {"total": 1, "size": 1},
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
            status=HTTPStatus.INTERNAL_SERVER_ERROR,
        )

        with pytest.raises(
            ServerError,
            match="There was a problem with retrieving" " metrics per country",
        ):
            await fetch_averaged_metrics_per_country(req)
