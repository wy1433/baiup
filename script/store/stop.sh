#!/bin/bash
path=store
proj=baikalStore
self_port=`grep port conf/gflags.conf | awk -F"=" '{print $2}'|sed 's/ //g'`
pid=`ps -ef | grep "supervise" | grep "${path}" |awk '{print $2}'`
if [ "$pid" ]; then
    echo "stop supervise : "$pid
    kill -9 $pid
fi

pid=`ps -ef | grep "$proj" |grep -v "grep" | grep $self_port | awk '{print $2}'`
if [ "$pid" ]; then
    echo "stop ${path}: "$pid
    kill -9 $pid
fi
