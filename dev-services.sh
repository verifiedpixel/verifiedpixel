#!/bin/sh
docker-compose -p vpp -f docker/docker-compose-services.yml up -d mongodb elastic redis logstash postfix kibana
