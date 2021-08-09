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


class UpgradeProcessor():
    def __init__(self):
        self.pkgPath = "./repo"
        pass

    def usage(self):
        print "usage python main.py upgrade clustername version [module/node]"
        
    def init(self):
        if len(sys.argv) < 4:
            self.usage()
            exit(0)
        self.clusterName = sys.argv[2]
        self.version = sys.argv[3]
        msg = self.checkVersion()
        if msg != None:
            print msg
            exit(0)
        self.module = ''
        self.node = ''
        if len(sys.argv) >= 5:
            s = sys.argv[4]
            if s in ('meta','db','store'):
                self.module = s
            else:
                self.node = s
        
    def process(self):
        self.init()
        self.uuid = util.getNowStr()
        self.upgrade()
        
    def upgrade(self):
        self.deployConfig = DeployConfig.loadClusterDeployConfig(self.clusterName)
        rootDir = self.deployConfig["global"]["root_dir"]
        self.deployConfig = DeployConfig.loadClusterDeployConfig(self.clusterName)
        self.deployConfig['global']['version'] = self.version

        moduleList = ["meta","db","store"]
        localConfigDir = os.path.join("storage/oplist", self.uuid, "config")
        localDeployDir = os.path.join("storage/oplist", self.uuid, "deploy")
        ServerConfig.initServerConfig(self.deployConfig, localConfigDir)

        if self.module != '':
            moduleList = [self.module]
        upgradeCount = 0
        for module in moduleList:
            for instance in Instance.getInstanceListByDeployConfig(self.deployConfig, module):
                if self.node != '' and instance.node != self.node:
                    continue
                if upgradeCount != 0:
                    time.sleep(10)
		print "update bin, %s" % instance.node
                instance.updateRemoteBin()
                instance.updateRemoteConfig(os.path.join(localConfigDir, "%s.conf" % instance.node))
		instance.stop()
                instance.start()
                print "upgrade %s \033[1;32m succ \033[0m!" % instance.node
                upgradeCount += 1
        if upgradeCount == 0 and self.node != '':
            print "has no instance %s" % self.node
        DeployConfig.updateClusterDeployConfig(self.clusterName, self.deployConfig)


    def checkVersion(self):
        binPath = os.path.join(self.pkgPath, self.version, "bin")
        if not os.path.exists(binPath):
            return "has no version " + self.version
        for binName in ('baikaldb', 'baikalMeta', 'baikalStore'):
            binFile = os.path.join(binPath, binName)
            if not os.path.exists(binFile):
                return self.version + "'s " + binName + " not found!"
            if not os.access(binFile, os.X_OK):
                os.chmod(binFile, stat.S_IXGRP)

