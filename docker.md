cd path/To/Docker

docker build -t my-app-image .


docker run .... -e POSTGRES_PASSWORD=password


docker run --name redis -p 6379:6379 -d redis:7

docker ps

docker stop weather-redis
docker start weather-redis

docker rm weather-redis

docker compose up --build -d 
