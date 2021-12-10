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
from metaClient import MetaClient


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


    def getPhysicalRoomList(self):
        res = {}
        for store in self.deployConfig['store']:
            if 'config' not in store:
                continue
            if '-default_logical_room' not in store['config']:
                continue
            logicalRoom = store['config']['-default_logical_room']
            if logicalRoom not in res:
                res[logicalRoom] = []
            if '-default_physical_room' not in store['config']:
                continue
            physicalRoom = store['config']['-default_physical_room']
            if physicalRoom not in res[logicalRoom]:
                res[logicalRoom].append(physicalRoom)
        return res

    def getResourceTags(self):
        res = {}
        if 'server_configs' in self.deployConfig:
            if 'store' in self.deployConfig['server_configs']:
                if '-resource_tag' in self.deployConfig['server_configs']['store']:
                    res[self.deployConfig['server_configs']['store']['-resource_tag']] = 1
        for store in self.deployConfig['store']:
            if 'config' not in store:
                continue
            if '-resource_tag' not in store['config']:
                continue
            res[store['config']['-resource_tag']] = 1
        if len(res) == 0:
            res[''] = 1
        return res.keys()

    def deploy(self):
        configDir = os.path.join(CLUSTER_DIR, self.clusterName, "cache-conf")

        ServerConfig.initServerConfig(self.deployConfig, configDir)

        self.physicalRooms = self.getPhysicalRoomList()
        self.resourceTags = self.getResourceTags()
        self.metaList = DeployConfig.getMetaList(self.deployConfig)
        self.metaClient = MetaClient(','.join(self.metaList))
        for module in ('meta', 'store', 'db'):
            instanceList = Instance.getInstanceListByDeployConfig(self.deployConfig, module)
            scriptDir = os.path.join(CLUSTER_DIR, self.clusterName, "cache-conf")
            for instance in instanceList:
                print instance.node, "init"
                if instance.check():
                    print "instance %s has been inited!" % instance.node
                    continue
                instance.makeRemoteDir()

                instance.updateRemoteBin()
                instance.updateRemoteConfig(os.path.join(configDir, "%s.conf" % instance.node))
                instance.initScript(scriptDir)
                instance.updateRemoteScript(scriptDir)


            for instance in instanceList:
                if instance.check():
                    print "instance %s has been started!" % instance.node
                    continue
                instance.start()
                time.sleep(2)
                if instance.check():
                    print "start %s succ" % (instance.node)
                else:
                    print "start %s faild" % (instance.node)
                    exit(1)
            if module == 'meta':
                self.initMeta()
            
            if module == 'store':
                self.initDB()
                

    def initDB(self):
        self.metaClient.createNamespace("INTERNAL")
        self.metaClient.createDatabase("INTERNAL", "baikaldb")
        interTableInfo = {
            "table_name": "__baikaldb_instance",
            "resource_tag": self.resourceTags[0],
            "fields": [ 
                {
                    "field_name" : "instance_id",
                    "mysql_type" : "UINT64",
                    "auto_increment" : True
                }
            ],
            "indexs": [ 
                {
                    "index_name" : "priamry_key",
                    "index_type" : "I_PRIMARY",
                    "field_names": ["instance_id"]
                }
            ]
        }
        self.metaClient.createTable("INTERNAL","baikaldb", interTableInfo)
        

    def initMeta(self):
        # init meta
        # step 1 add logical room
        if len(self.physicalRooms) == 0:
            self.metaClient.addLogicalRoom(['default'])
            self.metaClient.addPhysicalRoom('default',['default'])
            return
        logicalRoomList = self.physicalRooms.keys()
            
        self.metaClient.addLogicalRoom(logicalRoomList)
        # step 2 add physical room
        for logicalRoom, physicalRoomList in self.physicalRooms.items():
            if len(physicalRoomList) == 0:
                self.metaClient.addPhysicalRoom(logicalRoom, ['default'])
                continue
            self.metaClient.addPhysicalRoom(logicalRoom, physicalRoomList)
                

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


