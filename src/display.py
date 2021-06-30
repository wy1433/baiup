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
        print "python main.py display clustername"

    def process(self):
        if len(sys.argv) != 3:
            self.usage()
            exit(0)
        self.clusterName = sys.argv[2]
	self.deployConfig = DeployConfig.loadClusterDeployConfig(self.clusterName)
        self.rootDir = self.deployConfig["global"]["root_dir"]
        self.displayCluster()

    def displayCluster(self):
        metaList = DeployConfig.getMetaList(self.deployConfig)
        metaClient = MetaClient(','.join(metaList))
        for mod in ("meta","store","db"):
            for instance in Instance.getInstanceListByDeployConfig(self.deployConfig, mod):
                key = instance.node
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

    

