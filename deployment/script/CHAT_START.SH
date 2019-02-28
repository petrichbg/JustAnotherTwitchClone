#!/bin/sh
if test -e /tmp/osp_chat.pid; then
    echo "/tmp/osp_chat.pid is already present"
    exit 1
fi

cd /home/stream/chat/
screen -dmS osp_chat nodejs chatServer.js -log /var/log/chatlogs/ -pidfilepath /tmp/osp_chat.pid