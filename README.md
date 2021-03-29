# yandex_backend_school_2021

Выполненное вступительное задание в Школу бэкенд-разработки Яндекса набор 2021.

Приложение упаковано в Docker контейнер. Приложение работает с БД Postgresql, для этого необнодимо передать через переменные окружения 2 переменные:
DB_URL в формате postgresql+asyncpg://username:password@host:port/db_name (основной DSN) и DB_SYNC_URL в формате postgresql://username:password@host:port/db_name (DSN для создания схемы БД).

Приложение поднимается на порту :8080. В приложении есть Swagger-документация по эндпоинту /docs

Приложение так же возможно и желательно поднимать через Docker-compose.

Все необходимые зависимости указаны в requirements.txt
