from enum import Enum, unique
import os
import sys
from sqlalchemy.engine import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.schema import Column, ForeignKey
from sqlalchemy.sql.sqltypes import Enum as dbEnum, Float, Integer, TIMESTAMP
from sqlalchemy.orm import relationship


@unique
class CourierType(Enum):
    foot = "foot"
    bike = "bike"
    car = "car"


Base = declarative_base()


class CouriersTable(Base):
    __tablename__ = "couriers"
    id = Column(Integer, primary_key=True)
    courier_type = Column(
        dbEnum(CourierType, name="courier_type"),
        nullable=False,
    )
    regions = relationship(
        "CourierRegionsTable",
        cascade="all,delete-orphan",
        passive_deletes=True,
    )
    working_hours = relationship(
        "CourierWorkingHoursTable",
        cascade="all,delete-orphan",
        passive_deletes=True,
    )


class CourierRegionsTable(Base):
    __tablename__ = "courier_regions"
    id = Column(Integer, primary_key=True)
    courier_id = Column(
        Integer, ForeignKey("couriers.id", ondelete="CASCADE"), nullable=False
    )
    region = Column(Integer, nullable=False)


class CourierWorkingHoursTable(Base):
    __tablename__ = "courier_working_hours"
    id = Column(Integer, primary_key=True)
    courier_id = Column(
        Integer, ForeignKey("couriers.id", ondelete="CASCADE"), nullable=False
    )
    from_border = Column(Integer, nullable=False, index=True)
    to_border = Column(Integer, nullable=False, index=True)


class OrdersTable(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True)
    weight = Column(Float, nullable=False)
    region = Column(Integer, nullable=False)
    courier_id = Column(
        Integer, ForeignKey("couriers.id", ondelete="CASCADE"), nullable=True
    )
    assigned_at = Column(TIMESTAMP(timezone=True), nullable=True)
    completed_at = Column(TIMESTAMP(timezone=True), nullable=True)
    delivery_type = Column(
        dbEnum(CourierType, name="courier_type"),
        nullable=True,
    )
    order_hours = relationship(
        "OrderDeliveryHoursTable",
        cascade="all,delete-orphan",
        passive_deletes=True,
    )


class OrderDeliveryHoursTable(Base):
    __tablename__ = "order_delivery_hours"
    id = Column(Integer, primary_key=True)
    order_id = Column(
        Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )
    from_border = Column(Integer, nullable=False, index=True)
    to_border = Column(Integer, nullable=False, index=True)

db_url = os.getenv('DB_SYNC_URL')
if not db_url:
    sys.exit('no sync DB URL!')

engine = create_engine(db_url)
Base.metadata.create_all(engine)
