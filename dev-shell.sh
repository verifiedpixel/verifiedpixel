#!/bin/sh
docker-compose -p vpp -f docker/docker-compose-dev.yml run backend sh /opt/superdesk/scripts/fig_wrapper.sh bash
