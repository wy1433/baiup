#!/usr/bin/python
#-*- coding:utf8 -*-

import time
import os
import operator
import sys
import yaml
import paramiko
import subprocess
import util
import copy
from deployConfig import DeployConfig
from serverConfig import ServerConfig
from instance import Instance


class EditConfigProcessor():
    def __init__(self):
        self.pkgPath = "./package"
        pass

    def usage(self):
        print "usage python main.py edit-config clustername"
        
    def init(self):
        if len(sys.argv) < 3:
            self.usage()
            exit(0)
        self.clusterName = sys.argv[2]
        self.deployConfig = DeployConfig.loadClusterDeployConfig(self.clusterName)
        
    def process(self):
        self.init()
        self.editConfig()
        #self.updateConfig()

        
    def editConfig(self):
        self.uuid = util.getNowStr()

        #1 拷贝deploy.yaml
        dirName = os.path.join("./storage/oplist", self.uuid, "deploy")
        if os.path.exists(dirName) == False:
            os.makedirs(dirName)
        fileName = os.path.join(dirName, "deploy.yaml")
        if os.path.exists(fileName):
            os.remove(fileName)
        with open(fileName, 'w') as f:
             f.write(yaml.dump(self.deployConfig, default_flow_style = False))
             f.close()
        cmd = "vi %s" % (fileName)
        os.system(cmd)
        #1 比较是否有变化,只取config
        newDeployConfig = DeployConfig.load(fileName)
        oldDeployConfig = copy.deepcopy(self.deployConfig)
        self.mergeServerConfig(newDeployConfig, oldDeployConfig)
        eqConfig = operator.eq(self.deployConfig, oldDeployConfig)
        if eqConfig:
            print "config has no change!"
        else:
	    confirm = raw_input("确定是否要修改(Y/N):")
	    if confirm.strip() != 'Y':
		return
            self.deployConfig = oldDeployConfig
            self.updateConfig()
            DeployConfig.updateClusterDeployConfig(self.clusterName, self.deployConfig)
        
    def mergeServerConfig(self, config1, config2):
        if 'server_configs' in config1:
            config2['server_configs'] = config1['server_configs']
        instanceConfig = {}
        for instance in Instance.getInstanceListByDeployConfig(config1):
            if instance.config != None:
                key = "%s:%d" % (instance.host, instance.port)
                instanceConfig[key] = instance.config
        for module in ['meta','db','store']:
            idx = 0
            for ins in config2[module]:
                key = "%s:%d" % (ins['host'], ins['port'])
                if key in instanceConfig:
                    config2[module][idx]['config'] = instanceConfig[key]
                idx += 1
                
        
    def updateConfig(self):
        localConfigDir = os.path.join('./storage/oplist', self.uuid, 'config')
        oldConfigDir = os.path.join('./storage/clusters', self.clusterName, 'cache-conf')
        ServerConfig.initServerConfig(self.deployConfig, localConfigDir)
        instanceList = Instance.getInstanceListByDeployConfig(self.deployConfig)
        for module in ['meta','store','db']:
            for ins in Instance.getInstanceListByDeployConfig(self.deployConfig, module):
                oldConfigFile = os.path.join(oldConfigDir, "%s.conf" % ins.node)
                newConfigFile = os.path.join(localConfigDir, "%s.conf" % ins.node)
		print newConfigFile
		print oldConfigFile
                oldConfig = {}
                if os.path.exists(oldConfigFile):
                    oldConfig = ServerConfig.load(oldConfigFile)
                newConfig = ServerConfig.load(newConfigFile)
                if not operator.eq(oldConfig, newConfig):
                    ins.updateRemoteConfig(newConfigFile)
                    ins.restart()
                    time.sleep(2)
                    if ins.check():
                        print "start %s succ" % ins.node
                    else:
                        print "start %s faild" % ins.node
                        exit(0)
                    os.rename(newConfigFile, oldConfigFile)
                    

    def copyNewConfig(self):
        rootDir = self.deployConfig['global']['root_dir']
        for module in ['meta','store','db']:
            for ins in self.deployConfig[module]:
                host = ins['host']
                port = ins['port']
                path = ''
                if 'path' in ins:
                    path = ins['path']
                else:
                    path = util.getDefaultPath(name, port)
                localConfigPath = os.path.join("storage/clusters",self.clusterName,"config","%s-%d.conf" % (host, port))
                remoteConfigPath = os.path.join(rootDir, path, "config", "gflags.conf")
                if not util.execScpRemoteCommand(localConfigPath, remoteConfigPath):
                    print "scp config faild:", "%s-%d.conf" % (host, port)
                    exit(1)
                
