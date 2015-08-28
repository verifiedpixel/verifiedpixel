#!/bin/sh
python3 manage.py users:create -u admin -p admin -e 'admin@example.com' --admin=true
python3 manage.py app:initialize_data
