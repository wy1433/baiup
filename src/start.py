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
	self.resource_tag = None
        if len(sys.argv) >= 4:
            s = sys.argv[3]
            if s in ('meta','db','store'):
                self.module = s
	    elif s.startswith('resource_tag='):
		self.resource_tag = s[13:].strip()
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
		if self.node != '' and self.node != instance.node:
		    continue
		if self.resource_tag != None:
		    if '-resource_tag' not in instance.config:
			continue
		    if instance.config['-resource_tag'] != self.resource_tag:
		        continue
                instance.start()
                startCnt += 1
        if self.node != '' and startCnt == 0:
            print "has't node %s" % self.node
            exit(1)
