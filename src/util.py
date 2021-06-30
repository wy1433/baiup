#!/usr/bin/python
#-*- coding:utf8 -*-

import os
import sys
import commands
import yaml
import paramiko
import subprocess
import telnetlib
import time
from common import *


def execSSHCommand(ip, cmdlist):
    if type(cmdlist) == str:
        cmdlist = [cmdlist]
    pkey='/home/work/.ssh/id_rsa'
    key=paramiko.RSAKey.from_private_key_file(pkey)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip,username = 'work',pkey=key, port=58518)
    stdin,stdout,stderr=ssh.exec_command(';'.join(cmdlist), get_pty=True)
    
    infomsg = stdout.read()
    errmsg = stderr.read()
    ssh.close()
    if errmsg != '':
        print errmsg
        return False, errmsg
    return True, infomsg

def newExecSshCommand(ip, cmd):
    cmdnew = 'ssh -p 58518 work@%s "%s"' % (ip, cmd)
    return execShellCommand(cmdnew)

def execShellCommand(cmd):
    (status, output) = commands.getstatusoutput(cmd)
    if status != 0:
        print "exec command faild !" + cmd
        return False
    return True

def execScpRemoteCommand(host, localpath, remotepath):
    cmd = "scp -P58518 %s work@%s:%s" % (localpath, host, remotepath)
    return execShellCommand(cmd)

def execScpLocalCommand(host, localpath, remotepath):
    cmd = "scp -P58518 work@%s:%s %s" % (host, remotepath, localpath)
    return execShellCommand(cmd)


def getDefaultPath(ty, port):
    if ty == 'meta':
        return "meta"
    if ty == 'db':
        if port == 28282:
            return "db"
        elif port == 28283:
            return "db1"
        return "db"
    if ty == 'store':
        if port > 8119 or port < 8110:
            return None
        basePath = "store"
        if port == 8110:
            return basePath
        return basePath + str(port - 8110)
    return None



def checkNode(host, port):
    try:
        telnetlib.Telnet(host = host, port = port,timeout = 2)
        return True
    except Exception,e:
        return False

def getNowStr():
    return time.strftime("%Y%m%d%H%M%S", time.localtime())

def eTime2TimeStamp(etime):
    res = 0
    if etime.find('-') != -1:
        res = int(etime.split('-')[0]) * 86400
        etime = etime.split('-')[-1]
    ops = etime.split(':')
    tmp = 0
    for op in ops:
        tmp = tmp * 60 + int(op)
    res += tmp
    return res

def getStartTime(host, port, ty):
    binName = BIN_NAME_DICT[ty]
    pidcmd = 'ps aux | grep bin/%s | grep -v grep | grep %d | awk \'{print $2}\'' % (binName, port)
    if ty == 'meta':
        pidcmd = 'ps aux | grep bin/%s | grep -v grep | awk \'{print $2}\'' % binName
    code ,msg = execSSHCommand(host, pidcmd)
    if not msg.strip().isdigit():
        return None
    pid = int(msg)
    
    etimecmd = 'ps -p %d -o etime=' % (pid)
    code, msg = execSSHCommand(host, etimecmd)
    if code == False:
        return None
    ts = eTime2TimeStamp(msg.strip())
    return time.strftime("%Y-%m-%d %H:%M:%S" , time.localtime(time.time() - ts))

def getAliveTime(host, port, ty):
    binName = BIN_NAME_DICT[ty]
    pidcmd = 'ps aux | grep bin/%s | grep -v grep | grep %d | awk \'{print $2}\'' % (binName, port)
    if ty == 'meta':
        pidcmd = 'ps aux | grep bin/%s | grep -v grep | awk \'{print $2}\'' % binName
    code ,msg = execSSHCommand(host, pidcmd)
    if not msg.strip().isdigit():
        return None
    pid = int(msg)
    
    etimecmd = 'ps -p %d -o etime=' % (pid)
    code, msg = execSSHCommand(host, etimecmd)
    if code == False:
        return None
    ts = eTime2TimeStamp(msg.strip())
    if ts > 86400 :
        return "%dd" % int(ts / 86400)
    elif ts > 3600:
        return "%dh" % int(ts / 3600)
    elif ts > 60:
        return "%dm" % int(ts / 60)
    else:
        return "%ds" % int(ts)


if __name__ == '__main__':
    cmd = 'cd /home/work/BaikalDB_test/db && bash restart_by_supervise.sh'
    #print execSSHCommand('10.100.217.149',[cmd])
    #print checkNode("10.100.217.149",9010)
    print getStartTime('10.100.217.149',28282,'db')
