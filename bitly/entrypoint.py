"""
Bit.ly Backend Coding Challenge
"""

import math
from collections import defaultdict
from http import HTTPStatus

import asyncio
import aiohttp

_BITLY_BASE_URL = "https://api-ssl.bitly.com/v4"


def flatten(list_of_lists):
    """
    Takes a list of lists and flattens everything down to a single list
    :param list_of_lists: A list where the elements are lists
    """
    return (item for sublist in list_of_lists for item in sublist)


async def fetch_default_group_id(session):
    """
    Retrieves the default group id for the user that owns the used access token
    :param session: An aiohttp ClientSession to make requests with
    """
    async with session.get(f"{_BITLY_BASE_URL}/user") as response:
        if response.status == HTTPStatus.OK:
            return (await response.json())["default_group_guid"], True
        print(await response.text())
    return None, False


async def fetch_bitlink_ids(session, group_id):
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
        resp_json = await response.json()
        responses.append(resp_json)
        pagination = resp_json["pagination"]
        total = pagination["total"]
        size = pagination["size"]
        number_of_concurrent_requests_to_make = int(math.ceil(total / size))

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
            print(await response.text())
            return None, False

    links = flatten((response.get("links", {}) for response in responses))
    bitlinks = []
    for link in links:
        if "id" in link:
            bitlinks.append(link["id"])
        else:
            return None, False
    return bitlinks, True


async def fetch_clicks_per_country(session, bitlinks, *, unit="day", units=30):
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
            print(await response.text())
            return None, False

    metrics = flatten((response["metrics"] for response in responses))

    click_sums = defaultdict(int)
    for metric in metrics:
        click_sums[metric["value"]] += int(metric["clicks"])

    return click_sums, True


async def main(loop):
    """
    Main entrypoint of this application
    """
    headers = {"Authorization": "Bearer 2259b2b77fc1bda9ba43555fc983a24cb0104f0e"}
    async with aiohttp.ClientSession(loop=loop, headers=headers) as session:
        group_id, success = await fetch_default_group_id(session)
        if not success:
            print("Problem getting group id")
            return

        bitlinks, success = await fetch_bitlink_ids(session, group_id)
        if not success:
            print("Problem getting bitlink ids")
            return

        click_sums, success = await fetch_clicks_per_country(session, bitlinks)
        if not success:
            print("Problem getting bitlink metrics")
            return

        averaged = {country: clicks / 30 for country, clicks in click_sums.items()}
        print(averaged)


if __name__ == "__main__":
    LOOP = asyncio.get_event_loop()
    LOOP.run_until_complete(main(LOOP))
    LOOP.close()
