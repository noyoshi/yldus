#!/bin/sh

docker stop yldus-yay
docker rm yldus-yay
docker rmi -f yldus-yay
