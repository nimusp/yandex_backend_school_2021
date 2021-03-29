import logging
import os
import sys
from aiohttp import web
from aiohttp_pydantic import oas

from candy_delivery.db.dao import DAO, DAO_KEY
from candy_delivery.api.middleware import error_middleware

from candy_delivery.api.get_courier_stats import GetCourierStats
from candy_delivery.api.complete_order import CompleteOrder
from candy_delivery.api.assign_orders import AssignOrders
from candy_delivery.api.add_orders import AddOrders
from candy_delivery.api.update_courier import UpdateCourier
from candy_delivery.api.add_couriers import AddCouriers


log = logging.getLogger(__name__)

app = web.Application(middlewares=[error_middleware])

log.info("register handlers...")
app.add_routes(
    [
        web.post("/couriers", AddCouriers),
        web.patch("/couriers/{courier_id}", UpdateCourier),
        web.post("/orders", AddOrders),
        web.post("/orders/assign", AssignOrders),
        web.post("/orders/complete", CompleteOrder),
        web.get("/couriers/{courier_id}", GetCourierStats),
    ]
)

log.info('try to get DB URL...')
db_url = os.getenv('DB_URL')
if not db_url:
    sys.exit('no DB URL!')

log.info("setup docs...")
oas.setup(app, url_prefix="/docs")


async def on_startup(app):
    log.info("connect to DB...")
    app[DAO_KEY] = DAO(db_url)


app.on_startup.append(on_startup)


if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=8080)
