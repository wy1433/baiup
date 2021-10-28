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
import operator
from metaClient import MetaClient


class InitProcessor():
    def __init__(self):
        self.pkgPath = "./package"
        pass

    def usage(self):
        print "usage python main.py init clustername ./deploy.yaml"
        
    def init(self):
        if len(sys.argv) != 4:
            self.usage()
            exit(0)
        self.clusterName = sys.argv[2]
        self.configPath = sys.argv[3]
        self.deployConfig = DeployConfig.load(self.configPath)
        self.deployConfig['global']['cluster'] = self.clusterName
        
    def checkConfig(self):
        c = self.deployConfig
        if "global" not in c:
            c["global"] = {}
        if "root_dir" not in c['global']:
            c['global']['root_dir'] = '/home/work/BaikalDB'
        if "meta" not in c:
            return "has no found meta"
        ipportdict = {}
        self.metaList = []
        for t in ('meta', 'db', 'store'):
            if t not in c:
                continue
            for ins in c[t]:
                host = ins['host']
                if 'port' not in ins:
                    if t == 'meta':
                        ins['port'] = 8010
                    elif t == 'store':
                        ins['port'] = 8110
                    elif t == 'db':
                        ins['port'] = 28282
                port = ins['port']
                k = host + ':' + str(port)
                if t == 'meta':
                    self.metaList.append(k)
                if k in ipportdict:
                    return host + ":" + str(port) + " has same instance in " + ipportdict[k]
                ipportdict[k] = t
                if 'path' not in ins:
                    ins['path'] = util.getDefaultPath(t, port)

        
    def process(self):
        self.init()
        msg = self.checkConfig()
        if msg != None:
            print msg
            exit(0)
        self.initCluster()
        DeployConfig.updateClusterDeployConfig(self.clusterName, self.deployConfig)

        self.checkServerConfig()
        print "cluster %s init done" % (self.clusterName)

    def checkServerConfig(self):
        self.uuid = util.getNowStr()
        newConfigDir = os.path.join(LOCAL_CACHE_DIR, self.uuid, 'config')
        ServerConfig.initServerConfig(self.deployConfig, newConfigDir)
        for instance in Instance.getInstanceListByDeployConfig(self.deployConfig):
            key = instance.node
            oldConfigFile = os.path.join(CLUSTER_DIR, self.clusterName, "cache-conf", "%s.conf" % key)
            newConfigFile = os.path.join(newConfigDir, "%s.conf" % key)
            oldConfig = ServerConfig.load(oldConfigFile)
            newConfig = ServerConfig.load(newConfigFile)
            newConfig['-meta_server_bns'] = oldConfig['-meta_server_bns']
            if not operator.eq(oldConfig, newConfig):
                print "not eq:", oldConfigFile, newConfigFile
        
        
    def initCluster(self):
        configDir = os.path.join(CLUSTER_DIR, self.clusterName, "cache-conf")
        if not os.path.exists(configDir):
            os.makedirs(configDir)
        scriptDir = os.path.join(CLUSTER_DIR, self.clusterName, "script")
	if not os.path.exists(scriptDir):
	    os.makedirs(scriptDir)

        metaList = DeployConfig.getMetaList(self.deployConfig)
        metaClient = MetaClient(",".join(metaList))
        storeList = metaClient.getInstanceList()
        self.deployConfig['store'] = []
        for store in storeList:
            s = {"host":str(store.split(':')[0]), "port":int(store.split(':')[1])}
            self.deployConfig['store'].append(s)

        msg = self.checkConfig()
        if msg != None:
            print msg
            exit(0)

        cpuCoresDict = {}
	memLimitDict = {}
        packageConfig = ServerConfig.loadPkgServerConfig(self.deployConfig['global']['version'])
        for module in ('meta', 'store', 'db'):
            print module
            moduleConfig = {}
            if module in packageConfig:
                moduleConfig = packageConfig[module]

            instanceList = Instance.getInstanceListByDeployConfig(self.deployConfig, module)
            instanceCount = len(instanceList)
            commonConfigs = {}
            for instance in instanceList:
                configFileName = os.path.join(configDir, "%s.conf" % instance.node)
                instance.getRemoteConfig(configFileName)
                remoteConfig = ServerConfig.load(configFileName)
                for key, value in remoteConfig.items():
                    if key in ('-meta_server_bns','-meta_port','-baikal_port','-store_port'):
                        continue
                    if key in moduleConfig and value == moduleConfig[key]:
                        continue
                    wor = "%s\1%s" % (key, value)
                    if wor not in commonConfigs:
                        commonConfigs[wor] = {}
                    commonConfigs[wor][instance.node] = 1
	        runScriptFile = os.path.join(scriptDir, '%s_run.sh' % instance.node)
	        instance.getRemoteRun(runScriptFile)
	        cpuCores, memLimit = util.getCpuCoresMemLimit(runScriptFile)
	        if cpuCores != None:
		    cpuCoresDict[instance.node] = cpuCores
	        if memLimit != None:
		    memLimitDict[instance.node] = memLimit
            deployConfig = {}
            instanceConfigs = {}
            for key, value in commonConfigs.items():
                sk = key.split('\1')[0].strip()
                sv = key.split('\1')[1].strip()
                if len(value.keys()) == instanceCount:
                    #共同的参数
                    deployConfig[sk] = sv
                else:
                    for instance, _ in value.items():
                        if instance not in instanceConfigs:
                            instanceConfigs[instance] = {}
                        instanceConfigs[instance][sk] = sv
            if 'server_configs' not in self.deployConfig:
                self.deployConfig['server_configs'] = {}
            if module not in self.deployConfig['server_configs']:
                self.deployConfig['server_configs'][module] = {}
            for key, value in deployConfig.items():
                self.deployConfig['server_configs'][module][key] = value
            for ins in self.deployConfig[module]:
                key = "%s:%d" % (ins['host'], ins['port'])
                if key in instanceConfigs:
                    ins['config'] = instanceConfigs[key]




        for module in ('meta', 'store', 'db'):
	    for ins in self.deployConfig[module]:
		node = '%s:%d' % (ins['host'], ins['port'])
		if node in cpuCoresDict:
		    ins['cpu_cores'] = cpuCoresDict[node]
		if node in memLimitDict:
		    ins['mem_limit'] = memLimitDict[node]
	
