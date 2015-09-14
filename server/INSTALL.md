

We gonna use `ubuntu:trusty` as a base.



##### Install python3 and the build-time dependencies for c modules

Execute:

```sh
apt-get update && \
DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
python3 python3-dev python3-pip python3-lxml \
build-essential libffi-dev git mercurial \
libtiff5-dev libjpeg8-dev zlib1g-dev \
libfreetype6-dev liblcms2-dev libwebp-dev \
curl
```




##### Setup the environment





Export environment variables:

```sh
export PYTHONUNBUFFERED=1 \
C_FORCE_ROOT="False" \
CELERYBEAT_SCHEDULE_FILENAME=/tmp/celerybeatschedule.db
```



##### Install the dependencies

Copy from the repository dir:

```sh
cp -r requirements.txt /tmp/requirements.txt
```

Execute:

```sh
cd /tmp && pip3 install -U -r /tmp/requirements.txt
```




##### Copy application source code

Copy from the repository dir:

```sh
cp -r . /opt/superdesk
```

-------

Working directory is: `/opt/superdesk/`

To start the application execute:

```sh
honcho start 
```

Following ports will be used by the application:

```sh
5000, 5100
```
