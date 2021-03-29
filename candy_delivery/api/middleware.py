from http import HTTPStatus
import json
import logging
import traceback
from aiohttp import web

from candy_delivery.dto.dto import CDNoResultFound

from aiohttp.web_middlewares import middleware


log = logging.getLogger(__name__)


@middleware
async def error_middleware(request, handler):
    try:
        response = await handler(request)
        if 400 <= response.status < 500:
            error_body = json.loads(response.body)
            is_pydantic_validate_error = "loc" in error_body[0]
            if is_pydantic_validate_error:
                err = await format_pydantic_error(error_body, request)

            return web.json_response(
                {"validation_error": err}, status=HTTPStatus.BAD_REQUEST
            )

    except CDNoResultFound as ex:
        log.error(f"no data: {str(ex)}")
        log.exception(ex)
        return web.Response(body=ex.details, status=HTTPStatus.NOT_FOUND)

    except Exception as ex:
        log.error(f"internal error: {str(ex)}")
        log.exception(ex)
        return web.json_response(
            {"details": "internal error"},
            status=HTTPStatus.INTERNAL_SERVER_ERROR
        )

    return response


# only POST /couriers and POST /orders has custom response by task
async def format_pydantic_error(error_body, request):
    key, ids = "details", []
    for details in error_body:
        location_part = details["loc"]
        if len(location_part) > 1:
            request_body = await request.json()
            request_item = request_body[location_part[0]][location_part[1]]
            if "courier_id" in request_item:
                key = "couriers"
                ids.append(request_item["courier_id"])
            if "order_id" in request_item:
                key = "orders"
                ids.append(request_item["order_id"])

    if len(ids) > 0:
        return {key: [{"id": item_id} for item_id in ids]}

    return error_body
