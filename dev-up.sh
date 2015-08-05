#!/bin/sh
docker-compose -p vpp -f docker/docker-compose-dev.yml up --x-smart-recreate
