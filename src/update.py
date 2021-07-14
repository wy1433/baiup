#!/usr/bin/python
#-*- coding:utf8 -*-

import time
import os
import sys
import yaml
import paramiko
import subprocess
import util
import shutil
from deployConfig import DeployConfig
from serverConfig import ServerConfig
from instance import Instance


class UpdateProcessor():
    def __init__(self):
        self.pkgPath = "./package"
        pass

    def usage(self):
        print "usage python main.py update clustername config|script|ss.sh [module|node]"
        
    def init(self):
        if len(sys.argv) < 4:
            self.usage()
            exit(0)
        self.clusterName = sys.argv[2]
        self.deployConfig = DeployConfig.loadClusterDeployConfig(self.clusterName)
        self.updateType = sys.argv[3]

        if self.updateType not in ('script','config','run','stop.sh','restart_by_supervise.sh'):
            print "cmd faild!"
            self.usage()
            exit(1)


        self.node = ''
        self.module = ''
        if len(sys.argv) >= 5:
            tmp = sys.argv[4]
            if tmp in ('db','meta','store'):
                self.module = tmp
            else:
                self.node = tmp
        
        
    def process(self):
        self.init()
        self.update()

        
    def update(self):
        self.uuid = util.getNowStr()
        if self.updateType == 'config':
            self.updateConfig()
        elif self.updateType == 'bin':
            self.updateBin()
        else:
            self.updateScript()


    def updateConfig(self):
        configDir = os.path.join("./storage/oplist", self.uuid, "config")
        ServerConfig.initServerConfig(self.deployConfig, configDir)
        moduleList = ['meta','store','db']
        if self.module != '':
            moduleList = [self.module]
        for module in moduleList:
            for instance in Instance.getInstanceListByDeployConfig(self.deployConfig, module):
                if self.node != '' and self.node != instance.node:
                    continue
                configFile = os.path.join(configDir, "%s.conf" % instance.node)
                instance.updateRemoteConfig(configFile)
                instance.start()
                time.sleep(2)
                if not instance.check():
                    print "start %s faild!" % instance.node
                    exit(1)
                else:
                    print "start %s succ!" % instance.node
                oldConfigFile = os.path.join("storage/clusters", self.clusterName, "cache-conf", "%s.conf" % instance.node)
                shutil.copy(configFile, oldConfigFile)

                
    def updateScript(self):
        scriptDir = os.path.join("./storage/oplist", self.uuid, "script")
        moduleList = ['meta','store','db']
        if self.module != '':
            moduleList = [self.module]
        for module in moduleList:
            for instance in Instance.getInstanceListByDeployConfig(self.deployConfig, module):
                if self.node != '' and self.node != instance.node:
                    continue
                instance.initScript(scriptDir)
                scriptType = None
                if self.updateType != 'script':
                    scriptType = self.updateType
                instance.updateRemoteScript(scriptDir, scriptType)
                print "update %s succ!" % instance.node

                
