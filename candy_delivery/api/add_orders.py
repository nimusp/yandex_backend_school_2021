from http import HTTPStatus
from aiohttp import web
from aiohttp_pydantic.oas.typing import r201

from candy_delivery.api.schema import AddOrdersRequest, AddOrdersResponse
from candy_delivery.api.base_view import BaseView

from candy_delivery.dto.dto import OrderDTO


class AddOrders(BaseView):
    async def post(
        self, request: AddOrdersRequest
    ) -> r201[AddOrdersResponse]:
        orders = [
            OrderDTO(
                order_id=order.order_id,
                weight=order.weight,
                region=order.region,
                delivery_hours=self.parse_time(order.delivery_hours),
            )
            for order in request.data
        ]

        await self.dao.add_orders(orders)

        resp = AddOrdersResponse(
            orders=[{"id": order.order_id} for order in request.data]
        )
        return web.json_response(resp.dict(), status=HTTPStatus.CREATED)
