#!/usr/bin/python
#-*- coding:utf8 -*-

import os
import sys
import yaml
import paramiko
from common import CLUSTER_DIR

class DeployConfig():
    def __init__(self, name, configPath):
        self.name = name
        self.configPath = configPath
    @staticmethod
    def load(fname):
        with open(fname,'r') as f:
                return yaml.load(f)

    @staticmethod
    def loadClusterDeployConfig(clusterName):
        dirName = os.path.join(CLUSTER_DIR, clusterName)
        fileName = os.path.join(dirName, "deploy.yaml")
        if not os.path.exists(fileName):
            print "cluster", clusterName , "not found!"
            exit(1)
        return DeployConfig.load(fileName)
    
    @staticmethod
    def updateClusterDeployConfig(clusterName, deployConfig):
        dirName = os.path.join(CLUSTER_DIR, clusterName)
        fileName = os.path.join(dirName, "deploy.yaml")
        if not os.path.exists(dirName):
            os.makedirs(dirName)
        with open(fileName, 'w') as f:
            f.write(yaml.dump(deployConfig, default_flow_style = False))
            f.close()

    @staticmethod
    def getMetaList(deployConfig):
        metaList = []
        for ins in deployConfig['meta']:
            key = '%s:%d' % (ins['host'], ins['port'])
            metaList.append(key)
        return metaList
