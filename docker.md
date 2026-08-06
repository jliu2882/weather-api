cd path/To/Docker

docker build -t my-app-image .


docker run .... -e POSTGRES_PASSWORD=password


docker run --name redis -p 6379:6379 -d redis:7

docker ps

docker stop weather-redis
docker start weather-redis

docker rm weather-redis



# geenral more docker tips

docker compose up --build -d 

docker compose -f docker-compose.prod.yml up --build -d


docker exec -it container_name_fromdockercompose psql -U username_fromdockercompose -d db_name_fromdockercompose -c "\d"

docker exec -it dev_postgres psql -U todo_admin -d todo_app_db -c "SQL COMMAND"

docker compose logs -f



update schema sql 2 methods

docker compose down -v

docker exec -i dev_postgres psql -U todo_admin -d todo_app_db < ./db/schema.sql
