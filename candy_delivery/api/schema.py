from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Extra


class CourierType(Enum):
    foot = "foot"
    bike = "bike"
    car = "car"


class Courier(BaseModel, extra=Extra.forbid):
    courier_id: int
    courier_type: CourierType
    regions: List[int]
    working_hours: List[str] = []


class AddCouriersRequest(BaseModel, extra=Extra.forbid):
    data: List[Courier]


class UpdateCourierRequest(BaseModel, extra=Extra.forbid):
    courier_type: Optional[CourierType]
    regions: List[int] = []
    working_hours: List[str] = []


class Order(BaseModel, extra=Extra.forbid):
    order_id: int
    weight: float
    region: int
    delivery_hours: List[str]


class AddOrdersRequest(BaseModel, extra=Extra.forbid):
    data: List[Order]


class CompleteOrderRequest(BaseModel, extra=Extra.forbid):
    courier_id: int
    order_id: int
    complete_time: str


class AssignOrdersRequest(BaseModel, extra=Extra.forbid):
    courier_id: int


class IdResponse(BaseModel):
    id: int


class AddCouriersResponse(BaseModel):
    couriers: List[IdResponse]


class AddOrdersResponse(BaseModel):
    orders: List[IdResponse]


class UpdateCourierResponse(BaseModel):
    courier_id: int
    courier_type: str
    regions: List[int] = []
    working_hours: List[str] = []


class AssignOrdersResponse(BaseModel):
    orders: List[IdResponse] = []
    assign_time: Optional[str]


class CompleteOrderResponse(BaseModel):
    order_id: int


class GetCourierStatsResponse(BaseModel):
    courier_id: int
    courier_type: str
    regions: List[int] = []
    working_hours: List[str] = []
    rating: Optional[float]
    earnings: Optional[int]
