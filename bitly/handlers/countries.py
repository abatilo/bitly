"""
Methods for handling any requests dealing with countries
"""
import math
import logging
from collections import defaultdict
from http import HTTPStatus

import asyncio
import aiohttp

from sanic.response import json
from sanic.exceptions import ServerError

from bitly.util import flatten

_BITLY_BASE_URL = "https://api-ssl.bitly.com/v4"

logger = logging.getLogger('root')

async def _fetch_default_group_id(session):
    """
    Retrieves the default group id for the user that owns the used access token
    :param session: An aiohttp ClientSession to make requests with
    """
    async with session.get(f"{_BITLY_BASE_URL}/user") as response:
        if response.status == HTTPStatus.OK:
            return (await response.json())["default_group_guid"], True
        log.error(await response.text())
    return None, False


async def _fetch_bitlink_ids(session, group_id):
    """
    Retrieves a list of all of the bitlink ids that belong to a given group
    :param session: An aiohttp ClientSession to make requests with
    :param group_id: The group id whose bitlinks we want to retrieve
    """
    first_page = f"{_BITLY_BASE_URL}/groups/{group_id}/bitlinks"
    number_of_concurrent_requests_to_make = 0

    responses = []

    # First request to get total number of links
    async with session.get(first_page) as response:
        if response.status == HTTPStatus.OK:
            resp_json = await response.json()
            responses.append(resp_json)
            pagination = resp_json["pagination"]
            total = pagination["total"]
            size = pagination["size"]
            number_of_concurrent_requests_to_make = int(math.ceil(total / size))
        else:
            log.error(await response.text())
            return None, False

    coroutines = (
        session.get(
            f"{_BITLY_BASE_URL}/groups/{group_id}/bitlinks",
            params={"page": page_number},
        )
        for page_number in range(2, number_of_concurrent_requests_to_make + 1)
    )

    for response in await asyncio.gather(*coroutines):
        if response.status == HTTPStatus.OK:
            responses.append(await response.json())
        else:
            log.error(await response.text())
            return None, False

    links = flatten((response.get("links", {}) for response in responses))
    bitlinks = []
    for link in links:
        bitlinks.append(link["id"])
    return bitlinks, True


async def _fetch_clicks_per_country(session, bitlinks, *, unit="day", units=30):
    """
    Retrieves the number of bitlink clicks per country
    :param session: An aiohttp ClientSession to make requests with
    :param bitlinks: A collection of bitlink ids to use for the aggregation
    :param unit: The time interval to use to group the click counts
    :param units: The number of `unit` intervals to query for
    """
    params = {"unit": unit, "units": units}

    coroutines = (
        session.get(f"{_BITLY_BASE_URL}/bitlinks/{bitlink}/countries", params=params)
        for bitlink in bitlinks
    )

    responses = []
    for response in await asyncio.gather(*coroutines):
        if response.status == HTTPStatus.OK:
            responses.append(await response.json())
        else:
            log.error(await response.text())
            return None, False

    metrics = flatten((response["metrics"] for response in responses))

    click_sums = defaultdict(int)
    for metric in metrics:
        click_sums[metric["value"]] += int(metric["clicks"])

    return click_sums, True


async def fetch_averaged_metrics_per_country(req):
    """
    Calculates the average number of clicks on a bitlink, grouped by country, averaged
    over some period of time
    """
    headers = {"Authorization": req.token}
    async with aiohttp.ClientSession(headers=headers) as session:
        group_id, success = await _fetch_default_group_id(session)
        if not success:
            raise ServerError(
                "There was a problem retrieving the group id",
                HTTPStatus.INTERNAL_SERVER_ERROR,
            )

        bitlinks, success = await _fetch_bitlink_ids(session, group_id)
        if not success:
            log.error("Problem getting bitlink ids")
            raise ServerError(
                "There was a problem getting the bitlink ids for your group",
                HTTPStatus.INTERNAL_SERVER_ERROR,
            )

        unit = "day"
        units = 30
        click_sums, success = await _fetch_clicks_per_country(  # pylint: disable=too-many-function-args
            session, bitlinks, unit=unit, units=units
        )
        if not success:
            log.error("Problem getting bitlink metrics")
            raise ServerError(
                "There was a problem with retrieving metrics per country",
                HTTPStatus.INTERNAL_SERVER_ERROR,
            )

        metrics = {country: clicks / 30 for country, clicks in click_sums.items()}
        metrics["type"] = "clicks"
        averaged = {"unit": unit, "units": units, "metrics": metrics}
        return json(averaged)
