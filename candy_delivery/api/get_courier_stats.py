from typing import List
from aiohttp import web
from aiohttp_pydantic.oas.typing import r200
from sqlalchemy.exc import NoResultFound

from candy_delivery.api.schema import GetCourierStatsResponse
from candy_delivery.api.base_view import BaseView

from candy_delivery.dto.dto import (
    CDNoResultFound,
    CourierType,
    CourierWithOrdersDTO,
    OrderDTO,
)


class GetCourierStats(BaseView):
    async def get(self, courier_id: int, /) -> r200[GetCourierStatsResponse]:
        try:
            courier_orders = await self.dao.get_courier_with_completed_orders(
                courier_id
            )
        except NoResultFound as ex:
            raise CDNoResultFound(
                error=ex, details=f"no courier with courier ID {courier_id}"
            )

        resp = GetCourierStatsResponse(
                courier_id=courier_orders.courier.courier_id,
                courier_type=courier_orders.courier.courier_type.name,
                regions=[region for region in courier_orders.courier.regions],
                working_hours=self.format_time(
                    courier_orders.courier.working_hours
                ),
            )
        
        if len(courier_orders.orders) > 0:
            resp.rating = self._count_rating(courier_orders.orders),
            resp.earnings = self._count_earnings(courier_orders),

        return web.json_response(resp.dict())

    def _count_earnings(self, dto: CourierWithOrdersDTO) -> int:
        if len(dto.orders) == 0:
            return 0

        money = 0
        for order in dto.orders:
            C = 0
            if order.delivery_type == CourierType.foot:
                C = 2
            if order.delivery_type == CourierType.bike:
                C = 5
            if order.delivery_type == CourierType.car:
                C = 9

            money += 500 * C

        return money

    def _count_rating(self, orders: List[OrderDTO] = []):
        if len(orders) == 0:
            return 0

        orders_by_regions = dict()
        for order in orders:
            if order.region not in orders_by_regions:
                orders_by_regions[order.region] = []
            orders_by_regions[order.region].append(order)

        delivery_times = []
        for _, region_orders in orders_by_regions.items():
            region_orders.sort(key=lambda order: order.completed_at)
            diffs = []
            for i in range(len(region_orders)):
                diff = 0
                if i == 0:
                    diff = (
                        region_orders[i].completed_at
                        - region_orders[i].assigned_at
                    ).total_seconds()
                else:
                    diff = (
                        region_orders[i].completed_at
                        - region_orders[i - 1].completed_at
                    ).total_seconds()
                diffs.append(diff)

            delivery_times.append(sum(diffs) / len(diffs))

        t = min(delivery_times)
        raw_rating = (60 * 60 - min(t, 60 * 60)) / (60 * 60) * 5
        return round(raw_rating, 2)
