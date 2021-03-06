#!/usr/bin/python
#-*- coding:utf8 -*-

import os
import sys
CURRENT_PATH = os.getcwd()
filepath,filename=os.path.split(os.path.abspath(sys.argv[0]))
srcpath=os.path.join(filepath,"../src")
sys.path.append(srcpath)
import yaml
import paramiko
import subprocess
from deploy import DeployProcessor
from start import StartProcessor
from stop import StopProcessor
from display import DisplayProcessor
from upgrade import UpgradeProcessor
from update import UpdateProcessor
from editConfig import EditConfigProcessor
from scaleIn import ScaleInProcessor
from scaleOut import ScaleOutProcessor
from init import InitProcessor
from cluster import ClusterProcessor
    

def mainExecCommand():
    cmd = sys.argv[1]
    if cmd == 'deploy':
        processor = DeployProcessor()
    elif cmd == 'upgrade':
        processor = UpgradeProcessor()
    elif cmd == 'restart':
        processor = StartProcessor()
    elif cmd == 'stop':
        processor = StopProcessor()
    elif cmd == 'start':
        processor = StartProcessor()
    elif cmd == 'scale-in':
        processor = ScaleInProcessor()
    elif cmd == 'scale-out':
        processor = ScaleOutProcessor()
    elif cmd == 'display':
        processor = DisplayProcessor()
    elif cmd == 'update':
        processor = UpdateProcessor()
    elif cmd == 'edit-config':
        processor = EditConfigProcessor()
    elif cmd == 'init':
        processor = InitProcessor()
    elif cmd == 'cluster':
        processor = ClusterProcessor()
    processor.process()


def mainusage():
    print "xx.py dddd"

if __name__ == '__main__':
    if len(sys.argv) < 2:
        mainusage()
        exit(0)
    mainExecCommand()

