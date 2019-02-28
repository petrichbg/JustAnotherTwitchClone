# Just Another Twitch Clone

This platform allows people to watch and chat on streams that go through nginx-rtmp. It covers the basic functionality of any livestreaming service.

* Powered by [Python/Django](https://www.djangoproject.com/), [MariaDB](https://mariadb.org/) for platform, and [node.js](https://nodejs.org/en/) for chat
* Works on top of [nginx-rtmp-module](https://github.com/arut/nginx-rtmp-module)
* Support for both RTMP and HLS
* Basic login and following system
* Users do moderation on others' streams
* Chat server with ban support

**Note:** frontend is russian language only, and some code/content/sensitive_info used on the original server was taken out of this repo. This is not intended to be used by anyone.

## Legacy notes

This project started in mid of 2015 as an incentive to learn web programming, covering both backend and frontend; and also to provide streaming service for everyone living in [Norilsk](https://en.wikipedia.org/wiki/Norilsk), as it didn't have good internet access to allow people to stream (and watch streams) on Twitch or simillar services.

It was closed at the beginning of 2018, as Norilsk got *better* internet access that allowed for streaming. **The source code is now merely published as a backup, as a project that could be shown off, or something that you could base on.**

This was the first ever project that I'm very proud of, and I'm grateful for all basics that I've learned from it.

## Legacy installation notes (debian-based server)

I made these notes for myself in case of redeployment, they should not be taken for granted, some of it may not work today and might be vague.

**Make a dedicated user and group for the service**
```
add user group
addgroup web
useradd -G web stream
useradd -G web srvadmin
```

**Install required libraries**
```
apt-get install gcc
apt-get install make
apt-get install libssl-dev
apt-get install python3-pip
apt-get install libtiff5-dev libjpeg8-dev zlib1g-dev libfreetype6-dev liblcms2-dev libwebp-dev tcl8.6-dev tk8.6-dev python-tk
apt-get install git

add-apt-repository ppa:mc3man/trusty-media
apt-get update
apt-get install ffmpeg

apt-get install nodejs
```

**Create directories**
```
mkdir /var/www/stream/
chgrp web /var/www/stream/
mkdir /var/www/stream/streampreview/

mkdir /var/log/stream/
mkdir /var/log/stream/stream_play/
mkdir /var/log/stream/stream_publish/

mkdir /var/log/chatlogs/
```

**Setup MariaDB**
```
apt-get install mariadb-server libmariadbclient-dev

// setup database password and make a user with name: osp
```

**Setup nginx**
```
// download latest nginx source from: http://nginx.org/en/download.html
// download latest nginx-rtmp-module source from: https://github.com/arut/nginx-rtmp-module

// Extract source code in sepearate directories

// In nginx source code directory
./configure --add-module=/home/srvadmin/nginx/nginx-rtmp-module-master/ --without-http_rewrite_module

make
make install

// copy deployment/upstart contents to /etc/init, make /etc/init/nginx executable

// update list of init configs
/usr/sbin/update-rc.d -f nginx defaults
```

**Install required Python libraries**
```
pip3 install Django==1.8.3
pip3 install django-ipware
pip3 install Markdown
pip3 install mdx-del-ins
pip3 install mysqlclient
pip3 install Pillow
pip3 install bleach
pip3 install uwsgi
```

**Edit crontab**
```
0 0 * * * /home/stream/CHAT_NEW_LOG.SH
*/10 * * * * python3 /var/www/stream/manage.py updatesubscribercounts
*/30 * * * * python3 /var/www/stream/manage.py removeexpiredbans
```

Configure `osp_uwsgi.ini`, `settings.py`, `nginx.conf`

Unfortunately, further configuration and deployment/launch commentary has been left unclear



