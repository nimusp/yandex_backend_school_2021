from aiohttp import web
from aiohttp_pydantic.oas.typing import r200
from sqlalchemy.exc import NoResultFound

from candy_delivery.dto.dto import CDNoResultFound, CourierDTO

from candy_delivery.api.base_view import BaseView
from candy_delivery.api.schema import (
    UpdateCourierRequest, UpdateCourierResponse
)


class UpdateCourier(BaseView):

    async def patch(
        self, courier_id: int, /, request: UpdateCourierRequest
    ) -> r200[UpdateCourierResponse]:

        courier = CourierDTO(
            courier_id=courier_id,
            courier_type=request.courier_type,
            regions=request.regions,
            working_hours=self.parse_time(request.working_hours),
        )

        try:
            updated_model = await self.dao.update_courier(courier)
        except NoResultFound as ex:
            raise CDNoResultFound(
                error=ex, details=f"no result for courier ID {courier_id}"
            )

        return web.json_response(
            UpdateCourierResponse(
                courier_id=updated_model.id,
                courier_type=updated_model.courier_type.name,
                regions=[r.region for r in updated_model.regions],
                working_hours=self.format_time(updated_model.working_hours),
            ).dict()
        )
