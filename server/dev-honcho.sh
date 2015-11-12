#!/bin/sh
env USE_VERIFICATION_MOCK=True VERIFICATION_TASK_RETRY_INTERVAL=3 honcho start -f ../docker/Procfile 
