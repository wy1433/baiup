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
from common import *
from deployConfig import DeployConfig
from serverConfig import ServerConfig
from instance import Instance
from package import Package


class UpgradeProcessor():
    def __init__(self):
        self.pkgPath = REPO_DIR
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
        self.resource_tag = None
        if len(sys.argv) >= 5:
            s = sys.argv[4]
            if s in ('meta','db','store'):
                self.module = s
            elif s.startswith('resource_tag='):
                self.resource_tag = s[13:].strip()
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
        localConfigDir = os.path.join(LOCAL_CACHE_DIR, self.uuid, "config")
        localDeployDir = os.path.join(LOCAL_CACHE_DIR, self.uuid, "deploy")
        ServerConfig.initServerConfig(self.deployConfig, localConfigDir)

        if self.module != '':
            moduleList = [self.module]
        upgradeCount = 0
        for module in moduleList:
            for instance in Instance.getInstanceListByDeployConfig(self.deployConfig, module):
                if self.node != '' and instance.node != self.node:
                    continue
                if self.resource_tag != None:
                    if '-resource_tag' not in instance.config:
                        continue
                    if instance.config['-resource_tag'] != self.resource_tag:
                        continue
                if upgradeCount != 0:
                    time.sleep(10)
                print "%s  update bin" % instance.node
                instance.updateRemoteBin()
                instance.updateRemoteConfig(os.path.join(localConfigDir, "%s.conf" % instance.node))
                instance.restart()
                print "%s  upgrade \033[1;32m succ \033[0m!" % instance.node
                upgradeCount += 1
        if upgradeCount == 0 and self.node != '':
            print "has no instance %s" % self.node
        DeployConfig.updateClusterDeployConfig(self.clusterName, self.deployConfig)


    def checkVersion(self):
        pkg = Package(self.version)
        if not pkg.is_local():
            pkg.download()
        for binName in ('baikaldb', 'baikalMeta', 'baikalStore'):
            binPath = os.path.join(REPO_DIR, self.version, "bin")
            binFile = os.path.join(binPath, binName)
            if not os.path.exists(binFile):
                return self.version + "'s " + binName + " not found!"
            if not os.access(binFile, os.X_OK):
                os.chmod(binFile, stat.S_IXGRP)


