from datetime import datetime
from typing import List, Set, Tuple

from sqlalchemy.orm import selectinload
from sqlalchemy.orm.session import sessionmaker

from sqlalchemy.sql.expression import select
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio import AsyncSession

from candy_delivery.dto.dto import (
    CourierDTO,
    CourierWithOrdersDTO,
    OrderDTO,
    CourierType as CourierTypeDTO,
    WorkingHoursDTO,
)
from candy_delivery.db.schema import (
    CourierType,
    CouriersTable,
    CourierRegionsTable,
    CourierWorkingHoursTable,
    OrderDeliveryHoursTable,
    OrdersTable,
)


DAO_KEY = "storage"


class DAO:
    def __init__(self, dsn: str) -> None:
        self._engine = create_async_engine(dsn, echo=False)
        self._async_session = sessionmaker(
            self._engine, expire_on_commit=False, class_=AsyncSession
        )

    async def add_couriers(self, courier_list: List[CourierDTO]):
        couriers = []
        for courier in courier_list:
            courier_model = CouriersTable(
                id=courier.courier_id,
                courier_type=CourierType(courier.courier_type.value),
            )
            c_regions, c_hours = [], []

            for r in courier.regions:
                c_regions.append(
                    CourierRegionsTable(
                        courier_id=courier.courier_id,
                        region=r,
                    )
                )

            for parsed_time in courier.working_hours:
                c_hours.append(
                    CourierWorkingHoursTable(
                        courier_id=courier.courier_id,
                        from_border=parsed_time.from_border,
                        to_border=parsed_time.to_border,
                    )
                )

            courier_model.regions = c_regions
            courier_model.working_hours = c_hours
            couriers.append(courier_model)

        async with self._async_session() as session:
            session.add_all(couriers)
            await session.commit()

    async def update_courier(self, update_model: CourierDTO) -> CouriersTable:
        async with self._async_session() as session:
            async with session.begin():
                query = (
                    select(CouriersTable)
                    .filter(CouriersTable.id == update_model.courier_id)
                    .with_for_update(of=CouriersTable)
                    .options(
                        selectinload(CouriersTable.regions),
                        selectinload(CouriersTable.working_hours),
                    )
                )
                result = await session.execute(query)
                courier = result.scalars().one()

                query = (
                    select(OrdersTable)
                    .filter(OrdersTable.courier_id == update_model.courier_id)
                    .filter(OrdersTable.completed_at == None)
                    .with_for_update(of=OrdersTable)
                    .options(selectinload(OrdersTable.order_hours))
                )

                result = await session.execute(query)
                courier_orders = result.scalars().all()

                ids_to_drop = self._get_order_ids_to_drop(
                    courier_orders, courier, update_model
                )
                if len(ids_to_drop) > 0:
                    for i in range(len(courier_orders)):
                        if courier_orders[i].id in ids_to_drop:
                            courier_orders[i].courier_id = None
                            courier_orders[i].assigned_at = None

                if update_model.regions:
                    courier.regions = [
                        CourierRegionsTable(
                            courier_id=update_model.courier_id,
                            region=r,
                        )
                        for r in update_model.regions
                    ]
                if update_model.courier_type:
                    courier.courier_type = CourierType(update_model.courier_type.value)
                if update_model.working_hours:
                    courier.working_hours = [
                        CourierWorkingHoursTable(
                            courier_id=update_model.courier_id,
                            from_border=hours.from_border,
                            to_border=hours.to_border,
                        )
                        for hours in update_model.working_hours
                    ]

                return courier

    def _get_order_ids_to_drop(
        self,
        orders: List[OrdersTable],
        courier: CouriersTable,
        update_model: CourierDTO,
    ) -> Set[int]:
        ids_to_drop = set()
        if len(orders) == 0:
            return ids_to_drop

        if update_model.courier_type:
            old_max_weight = self._get_courier_max_orders_weight(
                courier.courier_type
            )
            new_max_weight = self._get_courier_max_orders_weight(
                update_model.courier_type
            )
            if new_max_weight < old_max_weight:
                delta = old_max_weight - new_max_weight
                orders.sort(key=lambda order: order.weight, reverse=True)
                for order in orders:
                    ids_to_drop.add(order.id)
                    delta -= order.weight
                    if delta < 0:
                        break

        if update_model.regions:
            new_regions = set(update_model.regions)
            ids_to_drop.update(
                {o.id for o in orders if o.region not in new_regions}
            )

        if update_model.working_hours:
            for order in orders:
                if not self._is_order_fits(update_model.working_hours, order):
                    ids_to_drop.add(order.id)

        return ids_to_drop

    def _is_order_fits(
        self,
        new_delivery_hours: List[Tuple[int, int]],
        order_hours: List[OrderDeliveryHoursTable],
    ) -> bool:
        for order_delivery_hours in order_hours:
            for courier_delivery_hours in new_delivery_hours:
                from_border, to_border = (
                    courier_delivery_hours[0],
                    courier_delivery_hours[1],
                )
                if (
                    order_delivery_hours.from_border >= from_border
                    and order_delivery_hours.to_border <= to_border
                ):
                    return True

        return False

    async def add_orders(self, orders_list: List[OrderDTO]):
        orders = []
        for order in orders_list:
            o = OrdersTable(
                id=order.order_id,
                weight=order.weight,
                region=order.region
            )
            o.order_hours = [
                OrderDeliveryHoursTable(
                    order_id=order.order_id,
                    from_border=hours.from_border,
                    to_border=hours.to_border,
                )
                for hours in order.delivery_hours
            ]
            orders.append(o)

        async with self._async_session() as session:
            session.add_all(orders)
            await session.commit()

    async def complete_order(
        self, courier_id: int, order_id: int, complete_time: datetime
    ):
        async with self._async_session() as session:
            query = (
                select(OrdersTable)
                .filter(OrdersTable.id == order_id)
                .filter(OrdersTable.courier_id == courier_id)
            )

            result = await session.execute(query)
            order = result.scalars().one()

            order.completed_at = complete_time
            await session.commit()

    async def assign_orders(
        self, courier_id: int, assign_time: datetime
    ) -> List[int]:
        async with self._async_session() as session:
            async with session.begin():
                query = (
                    select(CouriersTable)
                    .filter(CouriersTable.id == courier_id)
                    .options(
                        selectinload(CouriersTable.regions),
                        selectinload(CouriersTable.working_hours),
                    )
                )
                result = await session.execute(query)
                courier = result.scalars().one()

                query = (
                    select(OrdersTable)
                    .filter(OrdersTable.courier_id == None)
                    .filter(
                        OrdersTable.region.in_(
                            [reg.region for reg in courier.regions]
                        )
                    )
                    .filter(
                        OrdersTable.order_hours.any(
                            OrderDeliveryHoursTable.from_border
                            >= CourierWorkingHoursTable.from_border
                        )
                    )
                    .filter(
                        OrdersTable.order_hours.any(
                            OrderDeliveryHoursTable.to_border
                            <= CourierWorkingHoursTable.to_border
                        )
                    )
                    .order_by(OrdersTable.id)
                    .with_for_update(of=OrdersTable)
                    .options(selectinload(OrdersTable.order_hours))
                )

                result = await session.execute(query)
                orders = result.scalars().all()
                if len(orders) == 0:
                    return []

                query = select(OrdersTable).filter(
                    OrdersTable.courier_id == courier_id
                )
                result = await session.execute(query)
                assigned_orders = result.scalars().all()

                max_weight = self._get_courier_max_orders_weight(
                    courier.courier_type
                )
                assigned_weight = max(
                    sum([o.weight for o in assigned_orders]),
                    0,
                )
                remained_weight = max_weight - assigned_weight
                if remained_weight <= 0:
                    return []

                # only number of orders matters by task
                orders.sort(key=lambda order: order.weight)
                ids_to_assign = []
                for order in orders:
                    if remained_weight - order.weight < 0:
                        break

                    ids_to_assign.append(order.id)
                    remained_weight -= order.weight
                    order.courier_id = courier_id
                    order.assigned_at = assign_time
                    order.delivery_type = courier.courier_type

                return ids_to_assign

    async def get_courier_with_completed_orders(
        self, courier_id: int
    ) -> CourierWithOrdersDTO:
        async with self._async_session() as session:
            courier_query = (
                select(CouriersTable)
                .filter(CouriersTable.id == courier_id)
                .options(
                    selectinload(CouriersTable.regions),
                    selectinload(CouriersTable.working_hours),
                )
            )
            result = await session.execute(courier_query)
            courier = result.scalars().one()

            orders_query = (
                select(OrdersTable)
                .filter(OrdersTable.courier_id == courier_id)
                .filter(OrdersTable.completed_at != None)
            )
            result = await session.execute(orders_query)
            orders = result.scalars().all()

            return CourierWithOrdersDTO(
                courier=CourierDTO(
                    courier_id=courier.id,
                    courier_type=CourierTypeDTO(courier.courier_type.value),
                    regions=[r.region for r in courier.regions],
                    working_hours=[
                        WorkingHoursDTO(
                            from_border=h.from_border, to_border=h.to_border
                        )
                        for h in courier.working_hours
                    ],
                ),
                orders=[
                    OrderDTO(
                        id=o.id,
                        region=o.region,
                        assigned_at=o.assigned_at,
                        completed_at=o.completed_at,
                        delivery_type=CourierTypeDTO(o.delivery_type.value),
                    )
                    for o in orders
                ],
            )

    def _get_courier_max_orders_weight(self, courier_type: CourierType) -> int:
        if courier_type == CourierType.foot or courier_type == CourierTypeDTO.foot:
            return 10
        if courier_type == CourierType.bike or courier_type == CourierTypeDTO.bike:
            return 15
        if courier_type == CourierType.car or courier_type == CourierTypeDTO.car:
            return 50
