#!/usr/bin/python
#-*- coding:utf8 -*-

import os
import sys
import yaml
import paramiko
import subprocess
from deployConfig import DeployConfig
import util
import time
from instance import Instance

class StartProcessor():
    def __init__(self):
        pass
    def usage(self):
        print "python deploy.py start clustername [module/node]"

    def process(self):
        if len(sys.argv) < 3:
            self.usage()
            exit(0)
        self.clusterName = sys.argv[2]
        self.deployConfig = DeployConfig.loadClusterDeployConfig(self.clusterName)
        self.rootDir = self.deployConfig["global"]["root_dir"]
        self.module = ''
        self.node = ''
        if len(sys.argv) >= 4:
            s = sys.argv[3]
            if s in ('meta','db','store'):
                self.module = s
            else:
                self.node = s
        self.startCluster()

    def startCluster(self):
        startCnt = 0
        moduleList = ['meta','store','db']
        if self.module != '':
            moduleList = [self.module]
        for mod in moduleList:
            instanceList = Instance.getInstanceListByDeployConfig(self.deployConfig, mod)
            for instance in instanceList:
                key = instance.node
                if key == self.node or self.node == '':
                    #print "start instance %s" % key
                    instance.start()
                    #time.sleep(2)
                    #checkRet = instance.check()
                    #if checkRet :
                    #    print "start instance %s \033[1;32m succ \033[0m!" % key
                    #else:
                    #    print "start instance %s \033[1;31m faild \033[0m!" % key
                    #    exit(1)
                    startCnt += 1
        if self.node != '' and startCnt == 0:
            print "has't node %s" % self.node
            exit(1)
