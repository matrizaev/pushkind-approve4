#!/bin/bash

docker-compose up --build -d

if [ "$1" = "test" ]
then
    docker exec -it pushkind-approve4_event-service_1 ./test.sh
    docker exec -it pushkind-approve4_hub-service_1 ./test.sh
    docker exec -it pushkind-approve4_order-service_1 ./test.sh
    docker exec -it pushkind-approve4_project-service_1 ./test.sh
    docker exec -it pushkind-approve4_tender-service_1 ./test.sh
    docker exec -it pushkind-approve4_user-service_1 ./test.sh
elif [ "$1" = "deploy" ]
then
    docker exec -it pushkind-approve4_event-service_1 ./deploy.sh
    docker exec -it pushkind-approve4_hub-service_1 ./deploy.sh
    docker exec -it pushkind-approve4_order-service_1 ./deploy.sh
    docker exec -it pushkind-approve4_project-service_1 ./deploy.sh
    docker exec -it pushkind-approve4_tender-service_1 ./deploy.sh
    docker exec -it pushkind-approve4_user-service_1 ./deploy.sh
fi