#!/usr/bin/python
#-*- coding:utf8 -*-

import os
import sys
import yaml
import paramiko
import subprocess
from deployConfig import DeployConfig
import util
from metaClient import MetaClient
from instance import Instance

class DisplayProcessor():
    def __init__(self):
        pass
    def usage(self):
        print "python main.py display clustername [db|store|meta|node]"

    def process(self):
        if len(sys.argv) <= 3:
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

        self.displayCluster()

    def displayCluster(self):
        metaList = DeployConfig.getMetaList(self.deployConfig)
        metaClient = MetaClient(','.join(metaList))
	moduleList = ['meta','store','db']
	if self.module != '':
	    moduleList = [self.module]
        for mod in moduleList:
            for instance in Instance.getInstanceListByDeployConfig(self.deployConfig, mod):
                key = instance.node
		if self.node != '' and self.node != key:
		    continue
                checkRet = instance.check()
                if checkRet :
                    nodeStatus = 'UP'
                    if instance.type == 'store':
                        status = metaClient.getInstanceStatus(instance.node)
                        nodeStatus = status
                        if status == 'MIGRATE':
                            cnt = metaClient.getInstanceRegionCount(instance.node)
                            if cnt == 0:
                                nodeStatus = 'TOMBSTONE'
                    if nodeStatus not in ('UP','NORMAL'):
                        print "%s\t%s\t\t\t\033[5;35m %s \033[0m!" % (key, mod, nodeStatus)
                    else:
                        aliveTime = instance.getAliveTime()
                        print "%s\t%s\t\t%s\t\033[1;32m %s \033[0m!" % (key, mod, aliveTime, nodeStatus)
                else:
                    print "%s\t%s\t\t\t\033[5;31m DOWN \033[0m!" % (key,mod)

    

