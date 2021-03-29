from datetime import datetime
from aiohttp import web
from aiohttp_pydantic.oas.typing import r200
from sqlalchemy.exc import NoResultFound

from candy_delivery.dto.dto import CDNoResultFound

from candy_delivery.api.schema import (
    AssignOrdersRequest, AssignOrdersResponse, IdResponse
)
from candy_delivery.api.base_view import BaseView


class AssignOrders(BaseView):
    async def post(
        self, request: AssignOrdersRequest
    ) -> r200[AssignOrdersResponse]:
        assign_time = datetime.now()

        try:
            order_ids = await self.dao.assign_orders(
                request.courier_id, assign_time
            )
        except NoResultFound as ex:
            raise CDNoResultFound(
                error=ex,
                details=f"courier with id {request.courier_id} not found",
            )

        resp = AssignOrdersResponse(
            orders=[IdResponse(id=o_id) for o_id in order_ids],
            assign_time=assign_time.strftime(self.get_time_format())
            if len(order_ids) > 0
            else None,
        )
        return web.json_response(resp.dict())
