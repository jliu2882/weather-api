cd path/To/Docker

docker build -t my-app-image .


docker run .... -e POSTGRES_PASSWORD=password


docker run --name redis -p 6379:6379 -d redis:7

docker ps

docker stop weather-redis
docker start weather-redis

docker rm weather-redis


docker compose up --build -d 

docker exec -it dev_postgres psql -U todo_admin -d todo_app_db -c "\d"


update schema sql 2 methods

docker compose down -v

docker exec -it dev_postgres psql -U todo_admin -d todo_app_db -c "SQL COMMAND"

docker exec -i dev_postgres psql -U todo_admin -d todo_app_db < ./db/schema.sql
