# Backend Redis Microservice


## NOTES
#### CRUD operations for Docker Container
- To create + run a docker container:
    - `docker run -p port:port redis`
        - `run` - runs a container form an image
        - `-p port:port` - left: host machine, right: container's internal port
        - `redis` - image name
        - *Note:* Using `run` does not persist data, no auto restart, no name of container, no mount olumes, not store configuration, not scale to many devices
- To start a container:
    - `docker start <container>`
- To stop a container:
    - `docker stop <container>`
- To restart a container:
    - `docker restart <container>`
- To kill a container:
    - `docker kill <container>`
- To remove a stopped container:
    - `docker rm <container>`

#### Viewing Containers
- To view list of running containers;
    - `docker ps`
- To lit all containers:
    - `docker ps -a`

#### Logs & Shell Access
- To view container logs:
    - `docker logs <container>`
- Open interactive shell inside a running container:
    - `docker exec -it <container> bash`

#### Run a docker YML file
- Def: Defines each service and each service is used to create a container
- Go inside the directory and call `docker compose up -d`
    - `-d` - runs in background
    - Creates docker image if not created
- `docker compose logs -f redis`
    - `-f` - follows logs live
    - `redis` - filters to redis server name inside .yml file
- `docker compose ps`
    - Shows which services are working inside container
- Stop container:
    - `docker compose down`
- Docker automatically knows the `docker-compose.yml` name by convention

#### docker-compose.yml file
- Docker fetches redis image in file by doing `image: redis:latest` which includes:
    - `redis-server`
    - `redis-ci`

#### docker images
- Middle between having service initialized and creating container
    - Used inside the service
- Frozen environment that has everything to run
    - Includes importing app file like `app.py`
    - Python runttime
    - Literally everything
- To view docker images, do
    `docker images`
- To remove docker image, do
    `docker rmi -f <image_name>`

#### Redis Python Module
- `redis_app = redis.Redis(host="localhost", port=REDIS_PORT, decode_responses=True)`

#### Access Redis database
- `docker exec -it redis_cs361 redis-cli -a <password>`
    - `docker exec` - runs inside docker container
    - `-i` and `-t` - keeps stdn open, allocates a terminal
    - `redis_cs361` - name of docker container
    - `redis-cli` - activates redis cli
    - `-a password` - authenticate and ask for a password

#### Docker General
- `docker exec -it <container name> redis-cli -a <password>`

