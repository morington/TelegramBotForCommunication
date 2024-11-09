from typing import Optional

from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_response import Response
from jinja2 import Template
from redis.asyncio import Redis


async def router_errors(request: Request, template: Template, redis: Redis) -> Response:
    """
    Errors output `/errors`.

    :param request: Request object
    :param template: Jinja template
    :param redis: Redis client
    """
    error_id: Optional[str] = request.query.get('id')
    if not error_id:
        return web.Response(status=400, text='Error ID is required')

    traceback_bytes: bytes = await redis.get(error_id)
    traceback_str: str = traceback_bytes.decode('utf-8')
    data = {'log_traceback': traceback_str.replace("\\n", "<br>")}
    html_content = template.render(data)

    return web.Response(text=html_content, content_type='text/html')
