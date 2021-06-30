#!/usr/bin/python
#-*- coding:utf8 -*-

import os
import sys
import yaml
import time
import paramiko
import subprocess
from deployConfig import DeployConfig
import util
from common import CLUSTER_DIR
from instance import Instance

class StopProcessor():
    def __init__(self):
        pass
    def usage(self):
        print "python main.py stop clustername [meta|db|store] [node]"

    def process(self):
        if len(sys.argv) < 3:
            self.usage()
            exit(0)
        self.clusterName = sys.argv[2]
        self.loadDeployConfig()
        self.rootDir = self.deployConfig["global"]["root_dir"]
        self.module = ''
        self.node = ''
        if len(sys.argv) >= 4:
            s = sys.argv[3]
            if s in ('meta','db','store'):
                self.module = s
            else:
                self.node = s
        self.stopCluster()

    def stopCluster(self):
        stopCnt = 0
        moduleList = ['meta','store','db']
        if self.module != '':
            moduleList = [self.module]
        for mod in moduleList:
            for instance in Instance.getInstanceListByDeployConfig(self.deployConfig, mod):
                key = instance.node
                if key == self.node or self.node == '':
                    instance.stop()
                    stopCnt += 1
        if self.node != '' and stopCnt == 0:
            print "has't node %s" % self.node
            exit(1)


    def loadDeployConfig(self):
        dirName = os.path.join(CLUSTER_DIR, self.clusterName)
        fileName = os.path.join(dirName, "deploy.yaml")
        if not os.path.exists(fileName):
            print "cluster", self.clusterName , "not found!"
            exit(1)
        with open(fileName) as f:
                self.deployConfig = yaml.load(f)
    

