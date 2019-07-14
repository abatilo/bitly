"""
Bit.ly Backend Coding Challenge
"""

import asyncio
import aiohttp
import json
import math
from collections import defaultdict
from http import HTTPStatus

_BITLY_BASE_URL = "https://api-ssl.bitly.com/v4"


def flatten(list_of_lists):
    return (item for sublist in list_of_lists for item in sublist)


async def fetch_default_group_id(session):
    async with session.get(_BITLY_BASE_URL + "/user") as response:
        if response.status == HTTPStatus.OK:
            return (await response.json())["default_group_guid"], True
        print(await response.text())
    return None, False


async def fetch_bitlink_ids(session, group_id):
    first_page = f"https://api-ssl.bitly.com/v4/groups/{group_id}/bitlinks?page=1"
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
            f"https://api-ssl.bitly.com/v4/groups/{group_id}/bitlinks",
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
    params = {"unit": unit, "units": units}

    coroutines = (
        session.get(
            f"https://api-ssl.bitly.com/v4/bitlinks/{bitlink}/countries", params=params
        )
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
    h = {"Authorization": "Bearer 2259b2b77fc1bda9ba43555fc983a24cb0104f0e"}
    async with aiohttp.ClientSession(loop=loop, headers=h) as session:
        group_id, success = await fetch_default_group_id(session)
        if not success:
            print("Problem getting group id")

        bitlinks, success = await fetch_bitlink_ids(session, group_id)
        if not success:
            print("Problem getting bitlink ids")

        click_sums, success = await fetch_clicks_per_country(session, bitlinks)
        if not success:
            print("Problem getting bitlink metrics")
        averaged = {country: clicks / 30 for country, clicks in click_sums.items()}
        print(averaged)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))
    loop.close()
