#!/usr/bin/python
#-*- coding:utf8 -*-

import os
import sys
import yaml
import paramiko
import subprocess
import time
import util
from common import *
from deployConfig import DeployConfig
from serverConfig import ServerConfig
from instance import Instance


class DeployProcessor():
    def __init__(self):
        pass

    def usage(self):
        print "usage python deploy.py deploy clustername version config.yaml"
        
    def init(self):
        if len(sys.argv) != 5:
            self.usage()
            exit(0)
        self.clusterName = sys.argv[2]
        self.version = sys.argv[3]
        self.configPath = sys.argv[4]
        self.deployConfig = DeployConfig.load(self.configPath)
        self.deployConfig['global']['version'] = self.version
        self.deployConfig['global']['cluster'] = self.clusterName
        
    def checkConfig(self):
        c = self.deployConfig
        if "global" not in c or "root_dir" not in c["global"]:
            return "has no root dir"
        if "meta" not in c:
            return "has no found meta"
        if "db" not in c:
            return "has no found db"
        if "store" not in c:
            return "has no found store"
        ipportdict = {}
        self.metaList = []
        for t in ('meta', 'db', 'store'):
            if t not in c:
                return "has not found " + t
            for ins in c[t]:
                host = ins['host']
                port = ins['port']
                k = host + ':' + str(port)
                if t == 'meta':
                    self.metaList.append(k)
                if k in ipportdict:
                    return host + ":" + str(port) + " has same instance in " + ipportdict[k]
                ipportdict[k] = t
                if 'path' not in ins:
                    ins['path'] = util.getDefaultPath(t, port)
                    print k, ins['path']

        
    def process(self):
        self.init()
        msg = self.checkConfig()
        if msg != None:
            print msg
            exit(0)
        msg = self.checkVersion()
        if msg != None:
            print msg
            exit(0)

        DeployConfig.updateClusterDeployConfig(self.clusterName, self.deployConfig)
        self.deploy()
        
    def deploy(self):
        configDir = os.path.join(CLUSTER_DIR, self.clusterName, "cache-conf")

        ServerConfig.initServerConfig(self.deployConfig, configDir)

        for module in ('meta', 'store', 'db'):
            instanceList = Instance.getInstanceListByDeployConfig(self.deployConfig, module)
            scriptDir = os.path.join(CLUSTER_DIR, self.clusterName, "cache-conf")
            for instance in instanceList:
                instance.makeRemoteDir()

                instance.updateRemoteBin()
                instance.updateRemoteConfig(os.path.join(configDir, "%s.conf" % instance.node))
                instance.initScript(scriptDir)
                instance.updateRemoteScript(scriptDir)


            for instance in instanceList:
                instance.start()
                time.sleep(2)
                if instance.check():
                    print "start %s succ" % (instance.node)
                else:
                    print "start %s faild" % (instance.node)
                    exit(1)
                

    def checkVersion(self):
        binPath = os.path.join(REPO_DIR, self.version, "bin")
        if not os.path.exists(binPath):
            return "has no version " + self.version
        for binName in ('baikaldb', 'baikalMeta', 'baikalStore'):
            binFile = os.path.join(binPath, binName)
            if not os.path.exists(binFile):
                return self.version + "'s " + binName + " not found!"
            if not os.access(binFile, os.X_OK):
                os.chmod(binFile, stat.S_IXGRP)


