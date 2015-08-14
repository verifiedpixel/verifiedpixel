#!/bin/sh
docker-compose -p vpp -f docker/docker-compose-services.yml up -d mongo elastic redis logstash postfix kibana
