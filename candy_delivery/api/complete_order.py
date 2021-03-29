from candy_delivery.dto.dto import CDNoResultFound
from datetime import datetime
from aiohttp import web
from aiohttp_pydantic.oas.typing import r200
from sqlalchemy.exc import NoResultFound

from candy_delivery.api.schema import (
    CompleteOrderRequest, CompleteOrderResponse
)

from candy_delivery.api.base_view import BaseView


class CompleteOrder(BaseView):
    async def post(
        self, request: CompleteOrderRequest
    ) -> r200[CompleteOrderResponse]:
        completed_at = datetime.strptime(
            request.complete_time, self.get_time_format()
        )

        try:
            await self.dao.complete_order(
                request.courier_id, request.order_id, completed_at
            )
        except NoResultFound as ex:
            raise CDNoResultFound(
                error=ex,
                details=f"no data for courier ID {request.courier_id}" +
                f" or order ID {request.order_id}",
            )

        return web.json_response(
            CompleteOrderResponse(order_id=request.order_id).dict()
        )
