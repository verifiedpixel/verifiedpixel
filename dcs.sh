#!/bin/sh
docker-compose -p vpp -f docker/docker-compose-services.yml $@
