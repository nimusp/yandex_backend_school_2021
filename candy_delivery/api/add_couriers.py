from aiohttp import web
from aiohttp_pydantic.oas.typing import r201
from http import HTTPStatus

from candy_delivery.dto.dto import CourierDTO
from candy_delivery.api.schema import AddCouriersRequest, AddCouriersResponse
from candy_delivery.api.base_view import BaseView


class AddCouriers(BaseView):
    async def post(
        self, request: AddCouriersRequest
    ) -> r201[AddCouriersResponse]:
        couriers = []
        for courier in request.data:
            couriers.append(
                CourierDTO(
                    courier_id=courier.courier_id,
                    courier_type=courier.courier_type,
                    regions=[r for r in courier.regions],
                    working_hours=self.parse_time(courier.working_hours),
                )
            )

        await self.dao.add_couriers(couriers)

        resp = AddCouriersResponse(
            couriers=[{"id": courier.courier_id} for courier in request.data]
        )
        return web.json_response(resp.dict(), status=HTTPStatus.CREATED)
