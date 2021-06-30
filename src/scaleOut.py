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
import operator
from common import CLUSTER_DIR
from deployConfig import DeployConfig
from serverConfig import ServerConfig
from instance import Instance


class ScaleOutProcessor():
    def __init__(self):
        self.pkgPath = "./package"
        pass

    def usage(self):
        print "usage python main.py scale-out clustername ./scale-out.yaml"
        
    def init(self):
        if len(sys.argv) != 4:
            self.usage()
            exit(0)
        self.clusterName = sys.argv[2]
        self.deployConfig = DeployConfig.loadClusterDeployConfig(self.clusterName)
        self.scaleOutConfig = DeployConfig.load(sys.argv[3])
        
    def process(self):
        self.init()
        self.scaleOut()

    def mergeScaleOut2DeployConfig(self):

        self.oldInstanceDict = {}
        self.hostPathDict = {}
        for instance in Instance.getInstanceListByDeployConfig(self.deployConfig):
            key = instance.node
            self.oldInstanceDict[key] = instance
            hostPathKey = "%s:%s" % (instance.host, instance.path)
            self.hostPathDict[hostPathKey] = 1

        for module in ['meta','db','store']:
            if module not in self.scaleOutConfig:
                continue
            for ins in self.scaleOutConfig[module]:
                key = "%s:%d" % (ins['host'], ins['port'])
                if key not in self.oldInstanceDict:
                    self.deployConfig[module].append(ins)
                else:
                    print "instance %s exists" % key
                    exit(1)
                path = ''
                if 'path' in ins:
                    path = ins['path']
                else:
                    path = util.getDefaultPath(module, ins['port'])
                path = os.path.join(self.deployConfig['global']['root_dir'], path)
                hostPathKey = "%s:%s" % (ins['host'], ins['port'])
                if hostPathKey in self.hostPathDict:
                    print "path %s exist in %s" % (path, ins['host'])
                    exit(1)
                self.hostPathDict[hostPathKey] = 1

        
    def scaleOut(self):
        self.uuid = util.getNowStr()
        moduleList = ["meta","db","store"]

        self.mergeScaleOut2DeployConfig()
        configDir = os.path.join("storage/oplist", self.uuid, "config")
        scriptDir = os.path.join("storage/oplist", self.uuid, "script")

        oldConfigDir = os.path.join(CLUSTER_DIR, self.clusterName, "cache-conf")

        ServerConfig.initServerConfig(self.deployConfig, configDir)

        self.scaleOutInstanceList = []

        for module in ['meta','store','db']:
            for instance in Instance.getInstanceListByDeployConfig(self.deployConfig, module):
                if instance.node not in self.oldInstanceDict:
                    instance.makeRemoteDir()
                    instance.updateRemoteBin()
                    instance.updateRemoteConfig(os.path.join(configDir, "%s.conf" % instance.node))
                    instance.initScript(scriptDir)
                    instance.updateRemoteScript(scriptDir)
                    instance.start()
                    time.sleep(2)
                    if not instance.check():
                        print "start instance %s faild!" % instance.node
                        exit(1)
                    else:
                        print "start instance %s succ!" % instance.node

                oldConfigFile = os.path.join(oldConfigDir, "%s.conf" % instance.node)
                newConfigFile = os.path.join(configDir, "%s.conf" % instance.node)
                shutil.copy(newConfigFile, oldConfigFile)


        DeployConfig.updateClusterDeployConfig(self.clusterName, self.deployConfig)
        for module in ['meta','store','db']:
            for instance in Instance.getInstanceListByDeployConfig(self.deployConfig, module):
                oldConfigFile = os.path.join(oldConfigDir, "%s.conf" % instance.node)
                newConfigFile = os.path.join(configDir, "%s.conf" % instance.node)
                oldConfig = {}
                if os.path.exists(oldConfigFile):
                    oldConfig = ServerConfig.load(oldConfigFile)
                newConfig = ServerConfig.load(newConfigFile)
                if operator.eq(oldConfig, newConfig):
                    continue
                instance.start()
                time.sleep(2)
                if instance.check():
                    print "start %s succ!" % instance.node
                else:
                    print "start %s faild!" % instance.node
                    exit(1)
                shutil.copy(newConfigFile, oldConfigFile)
        

