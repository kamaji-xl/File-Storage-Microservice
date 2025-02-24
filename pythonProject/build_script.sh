#!/bin/bash


IMAGE_NAME="zmq-server"
CONTAINER_NAME="file_storage_microservice"
HOST=6000
PORT=5555

echo "Building Docker image: $IMAGE_NAME..."
docker build -t $IMAGE_NAME .

if docker ps -a --format '{{.Names}}' | grep -q "^$CONTAINER_NAME$"; then
    echo "Stopping and removing existing container: $CONTAINER_NAME..."
    docker stop $CONTAINER_NAME >/dev/null 2>&1
    docker rm $CONTAINER_NAME >/dev/null 2>&1
fi

echo "Starting new container..."
docker run -d -p $HOST:$PORT --name $CONTAINER_NAME $IMAGE_NAME

echo "Following logs..."
docker logs -f $CONTAINER_NAME
