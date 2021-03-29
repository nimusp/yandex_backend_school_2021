from datetime import datetime
from typing import List, Optional
from pydantic.main import BaseModel

from candy_delivery.api.schema import CourierType


class WorkingHoursDTO(BaseModel):
    from_border: int
    to_border: int


class CourierDTO(BaseModel):
    courier_id: Optional[int]
    courier_type: Optional[CourierType]
    regions: List[int] = []
    working_hours: List[WorkingHoursDTO] = []


class CouriersDTO(BaseModel):
    data: List[CourierDTO]


class OrderDTO(BaseModel):
    order_id: Optional[int]
    weight: Optional[float]
    region: Optional[int]
    delivery_hours: List[WorkingHoursDTO] = []
    assigned_at: Optional[datetime]
    completed_at: Optional[datetime]
    delivery_type: Optional[CourierType]


class OrdersDTO(BaseModel):
    data: List[OrderDTO] = []


class CourierWithOrdersDTO(BaseModel):
    courier: CourierDTO
    orders: List[OrderDTO] = []


class CDNoResultFound(Exception):
    def __init__(self, *args: object, error: object, details: str) -> None:
        super().__init__(*args)
        self.error = error
        self.details = details
    
    def __repr__(self) -> str:
        return f'details: {self.details}, ex: {self.error}'
