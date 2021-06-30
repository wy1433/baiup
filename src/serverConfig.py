#!/usr/bin/python
#-*- coding:utf8 -*-

from common import *
import copy
import os
import yaml
from deployConfig import DeployConfig
import util

class ServerConfig():
    def __init__(self):
        pass

    @staticmethod
    def load(fname):
        f = open(fname)
        res = {}
        for line in f:
            line = line.strip()
            if line == '':
                continue
            if line.startswith('-') == False:
                continue
            if line[0] == '#':
                continue
            pos = line.find('=')
            if pos == -1:
                res[line] = "true"
            else:
                key = line[:pos]
                value = line[pos + 1:]
                res[key] = value
        return res
    @staticmethod
    def dump(host, port, config, dirName):
        if os.path.exists(dirName) == False:
            os.makedirs(dirName)
        fileName = os.path.join(dirName, "%s:%d.conf" % (host, port))
        ServerConfig.write(fileName, config)

    @staticmethod
    def dumpNew(clusterName, host, port, config):
        dirName = os.path.join(CLUSTER_DIR, clusterName,"cache-conf")
        if os.path.exists(dirName) == False:
            os.makedirs(dirName)
        fileName = os.path.join(dirName, "%s-%d.conf.new" % (host, port))
        ServerConfig.write(fileName, config)


    @staticmethod
    def write(fileName, config):
        with open(fileName, 'w') as f:
            for key,value in config.items():
                f.write("%s=%s\n" % (key, value))

    @staticmethod
    def merge(source, dest):
        for key, value in source.items():
             if not key.startswith('-'):
                key = '-' + key
             dest[key] = value


    @staticmethod
    def initServerConfig(deployConfig, dirName):
        metaList = []
        serverPortFiledName = {"meta":"meta_port","db":"baikal_port","store":"store_port"}
        version = deployConfig['global']['version']
        clusterName = deployConfig['global']['cluster']
        for ins in deployConfig['meta']:
            metaList.append("%s:%d" % (ins['host'], ins['port']))
        metaList.sort()
        pkgServerConfig = {}
        if version != None:
            pkgServerConfig = ServerConfig.loadPkgServerConfig(version)
        commonServerConfig = {}
        if 'server_configs' in deployConfig:
            commonServerConfig = deployConfig['server_configs']
        for module in ['meta','store','db']:
            serverConfig = {}
            if module in pkgServerConfig:
                ServerConfig.merge(pkgServerConfig[module], serverConfig)
            serverConfig["-meta_server_bns"] = ",".join(metaList)
            if module in commonServerConfig:
                ServerConfig.merge(commonServerConfig[module], serverConfig)
            for ins in deployConfig[module]:
                instanceServerConfig = copy.deepcopy(serverConfig)
                if "config" in ins:
                     ServerConfig.merge(ins["config"], instanceServerConfig)
                instanceServerConfig["-" + serverPortFiledName[module]] = ins['port']
                
                ServerConfig.dump(ins['host'], ins['port'], instanceServerConfig, dirName)

    @staticmethod
    def loadPkgServerConfig(version):
        serverConfig = {}
        configPath = os.path.join(REPO_DIR, version, "conf")
        if not os.path.exists(configPath):
	    print configPath
	    print "package %s has not config" % version
	    exit(1)
        for module in ('db','meta','store'):
            subConfigFile = os.path.join(configPath, module + ".conf")
            if not os.path.exists(subConfigFile):
		print "%s has no config"
                continue
            subConfig = ServerConfig.load(subConfigFile)
            if module not in serverConfig:
                serverConfig[module] = {}
            for key, value in subConfig.items():
                serverConfig[module][key] = value
        return serverConfig


if __name__ == '__main__':
    deployConfig = DeployConfig.load("./test.yaml")
    print deployConfig
