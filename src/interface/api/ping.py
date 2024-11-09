from datetime import datetime

from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_response import Response


async def router_ping(_: Request) -> Response:
    """
    Checking the application's functionality `/ping`.

    :param _: Request object
    :return: { status": "OK", "datetime": "22.11.2023 17:46:00" }
    """

    return web.json_response({
        "status": "OK", "datetime": datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    })
