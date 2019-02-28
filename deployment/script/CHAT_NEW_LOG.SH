#!/bin/sh
if test -e /tmp/osp_chat.pid; then
    kill -s USR2 $( cat /tmp/osp_chat.pid )
fi