from typing import List
from aiohttp_pydantic import PydanticView

from candy_delivery.db.dao import DAO, DAO_KEY

from candy_delivery.dto.dto import WorkingHoursDTO
from candy_delivery.db.schema import CourierWorkingHoursTable


class BaseView(PydanticView):
    @property
    def dao(self) -> DAO:
        return self.request.app[DAO_KEY]

    def parse_time(self, str_times: List[str]) -> List[WorkingHoursDTO]:
        parsed = []
        for str_time in str_times:
            from_border, to_border = str_time.split("-")
            from_hours, from_minutes = from_border.split(":")
            to_hours, to_minutes = to_border.split(":")

            parsed.append(
                WorkingHoursDTO(
                    from_border=(int(from_hours) * 100 + int(from_minutes)),
                    to_border=(int(to_hours) * 100 + int(to_minutes)),
                ),
            )

        return parsed

    def format_time(
        self, db_times: List[CourierWorkingHoursTable]
    ) -> List[str]:
        formatted = []
        for raw in db_times:
            from_h, to_h = raw.from_border // 100, raw.to_border // 100
            from_hours = str(from_h) if from_h >= 10 else "0" + str(from_h)
            to_hours = str(to_h) if to_h >= 10 else "0" + str(to_h)

            from_m, to_m = raw.from_border % 100, raw.to_border % 100
            from_minutes = str(from_m) if from_m >= 10 else str(from_m) + "0"
            to_minutes = str(to_m) if to_m >= 10 else str(to_m) + "0"
            formatted.append(
                f"{from_hours}:{from_minutes}-{to_hours}:{to_minutes}"
            )

        return formatted

    def get_time_format(self) -> str:
        return "%Y-%m-%dT%H:%M:%S.%f%z"
