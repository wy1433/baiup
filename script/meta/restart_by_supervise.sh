#!/bin/bash
path=__REP_PATH__REP__
proj=baikalMeta
#self_port=`grep port conf/gflags.conf | awk -F"=" '{print $2}'|sed 's/ //g'`
pid=`ps -ef | grep "$proj" |grep -v "grep" | grep "$self_port" | awk '{print $2}'`
if [ "$pid" ]; then
    echo "stop: "$pid
    kill -2 $pid
fi

WAIT_SECS=600
wait_stop()
{
    time_left=$WAIT_SECS
    while [ $time_left -gt 0 ]
    do
        pid=`ps -ef | grep "$proj" |grep -v "grep" | grep "$self_port" | awk '{print $2}'`
        if [ "$pid" ]
        then
            echo "wait stop"
            sleep 1
            continue
        fi
        return 0
        time_left=$(($time_left-1))
    done
    echo "${proj} stop time(s) greater than ${WAIT_SECS}"
    exit 1
}
wait_stop

pid=`ps -ef | grep "supervise" | grep "${path}/" |awk '{print $2}'`
if [ "$pid" ]; then
    echo "supervise pid: "$pid
else
    nohup supervise ../$path/bin/ &
fi

# sleep 1
# pid=`ps -ef | grep "$proj" |grep -v "grep" | grep $self_port | awk '{print $2}'`
# echo "start: "$pid

WAIT_SECS=600
wait_start()
{
    time_left=$WAIT_SECS
    while [ $time_left -gt 0 ]
    do
        pid=`ps -ef | grep "$proj" |grep -v "grep" | grep "$self_port" | awk '{print $2}'`
        if [ $pid ]
        then
            echo "pid: $pid"
            return 0
        fi
        echo "wait start"
        sleep 1
        time_left=$(($time_left-1))
    done
    echo "${proj} start time(s) greater than ${WAIT_SECS}"
    exit 1
}

WAIT_SECS=600
wait_init_succ()
{
    time_left=$WAIT_SECS
    while [ $time_left -gt 0 ]
    do
        count=`grep "meta server init success" log/baikalMeta.WARNING | wc -l`
        if [ $count -gt 0 ]
        then
            echo "init success"
            return 0
        fi
        echo "wait init success"
        sleep 1
        time_left=$(($time_left-1))
    done
    echo "${proj} init time(s) greater than ${WAIT_SECS}"
    exit 1
}

wait_start
wait_init_succ
