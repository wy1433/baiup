#!/usr/bin/python
#-*- coding:utf8 -*-

import time
import os
import sys
import yaml
import paramiko
import subprocess
import shutil

import util
from deployConfig import DeployConfig
from serverConfig import ServerConfig
from instance import Instance
from metaClient import MetaClient


class ScaleInProcessor():
    def __init__(self):
        self.pkgPath = "./package"
        pass

    def usage(self):
        print "usage python main.py scale-in clustername node"
        
    def init(self):
        if len(sys.argv) != 4:
            self.usage()
            exit(0)
        self.clusterName = sys.argv[2]
        self.deployConfig = DeployConfig.loadClusterDeployConfig(self.clusterName)
        self.node = sys.argv[3]
        
    def process(self):
        self.init()
        self.scaleIn()

        
    def scaleIn(self):
        self.uuid = util.getNowStr()
        moduleList = ["meta","db","store"]
        scaleInType = ''
        haveScaleIn = False
        metaList = DeployConfig.getMetaList(self.deployConfig)
        droped = True
        for instance in Instance.getInstanceListByDeployConfig(self.deployConfig):
            key = instance.node
            if key != self.node:
                 continue
            scaleInType = instance.type

            if scaleInType == 'store':
                metaClient = MetaClient(','.join(metaList))
                status = metaClient.getInstanceStatus(key)
                if status == 'NORMAL':
                    #从meta set instance migrate
                    ret = metaClient.setInstanceMigrate(key)
                    if not ret :
                        print "set instance %s migrate faild!" % key
                        exit(1)
                    print "set instance %s migrate!" % key
                    droped = False
                    break
                elif status == 'MIGRATE':
                    cnt = metaClient.getInstanceRegionCount(key)
                    if cnt != 0:
                        droped = False
                        print "instance %s is migrating!" % key
                        break
                else:
                    print "instance %s status is %s, please check!" % (key, status)
                    exit(1)
                

            instance.stop()
            time.sleep(2)
            if instance.check():
                print "stop instance %s faild!" % key
                exit(1)
            print "stop instance %s succ!" % key
            instance.removeRemoteDir()
            haveScaleIn = True
        if not haveScaleIn:
            print "has no instance %s" % self.node

        #deploy config去掉节点
        if droped:
            for module in moduleList:
                newInsList = []
                for ins in self.deployConfig[module]:
                    key = "%s:%d" % (ins['host'], ins['port'])
                    if key != self.node:
                        newInsList.append(ins)
                self.deployConfig[module] = newInsList
        

        DeployConfig.updateClusterDeployConfig(self.clusterName, self.deployConfig)

        if scaleInType == 'meta':
	    self.updateConfig()

    def updateConfig(self):
        configDir = os.path.join("./storage/oplist", self.uuid, "config")
        oldConfigDir = os.path.join(CLUSTER_DIR, self.clusterName, "cache-conf")
        ServerConfig.initServerConfig(self.deployConfig, configDir)
        for instance in DeployConfig.getInstanceListByDeployConfig(self.deployConfig):
            configFileName = "%s.conf" % instance.node
            oldConfigFile = os.path.join(oldConfigDir, configFileName)
            newConfigFile = os.path.join(configDir, configFileName)
            oldConfig = ServerConfig.load(oldConfigFile)
            newConfig = ServerConfig.load(newConfigFile)
            if operator.eq(oldConfig, newConfig):
                continue
            instance.updateRemoteConfig(newConfigFile)
            instance.restart()
            time.sleep(2)
            if instance.check():
                print "start %s succ!" % instance.node
            else:
                print "start %s faild!" % instance.node
                exit(1)
            shutil.copy(newConfig, oldConfig)
