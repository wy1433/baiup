#!/bin/python
#-*- coding:utf8 -*-

import util
import os
import stat
import copy
import time
import sys
from common import *
from storeInteract import StoreInteract
from metaClient import MetaClient

class Instance():
    def __init__(self, host, port,clusterName,ty,version, path, metaList):
        self.clusterName = clusterName
        self.type = ty
        self.host = host
        self.port = port
        self.path = path
        self.subPath = self.path.split('/')[-1]
        self.version = version
        self.config = {}
        self.cpuCores = '0-255'
        self.memLimit = 512 * 1024 * 1024
        self.node = "%s:%d" % (self.host, self.port)
        if self.type == 'store':
            self.storeInteract = StoreInteract(self.host, self.port)
        self.metaList = metaList
        self.metaClient = MetaClient(','.join(self.metaList))


    def setConfig(self, config):
        self.config = copy.deepcopy(config)


    def initScript(self, dirName):
        if not os.path.exists(dirName):
            os.makedirs(dirName)
        tplDir = "./script"
        restartTplPath = os.path.join(tplDir, self.type, "restart_by_supervise.sh")
        restartData = open(restartTplPath).read().replace('__REP_PATH__REP__', self.subPath)
        stopTplPath = os.path.join(tplDir, self.type, "stop.sh")
        stopData = open(stopTplPath).read().replace('__REP_PATH__REP__', self.subPath)
        runData = open(os.path.join(tplDir, self.type, "run")).read()

        #run增加cpu cores和mem limit
        runData = runData.replace('__CPU_CORES_LIST__', self.cpuCores)
        runData = runData.replace('__MEM_LIMIT__', str(self.memLimit))

        
        nodeRestartFile = os.path.join(dirName, "restart_%s.sh" % self.node)
        open(nodeRestartFile ,'w').write(restartData)
        os.chmod(nodeRestartFile, stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)
        nodeStopFile = os.path.join(dirName, "stop_%s.sh" % self.node)
        open(nodeStopFile, 'w').write(stopData)
        os.chmod(nodeStopFile, stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)
        nodeRunFile = os.path.join(dirName, "run_%s.sh" % self.node)
        open(nodeRunFile, 'w').write(runData)
        os.chmod(nodeRunFile, stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)

        

        if self.type == 'db':
            nodeDummyPortFile = os.path.join(dirName, 'dummy_server_%s.port' % self.node)
            port = self.port
            dummy_port = 8888 + self.port - 28282
            dummyPortData = str(dummy_port)
            open(nodeDummyPortFile, 'w').write(dummyPortData)
            os.chmod(nodeDummyPortFile, stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)


    def updateRemoteScript(self, scriptDir, scriptName = None):
        scriptList = ['restart_by_supervise.sh','stop.sh','run']
        if self.type == 'db':
            scriptList = ['restart_by_supervise.sh','stop.sh','run','dummy_server.port']
        if scriptName != None and scriptName in scriptList:
            scriptList = [scriptName]


        for scriptName in scriptList:
            remoteDir = self.path
            if scriptName == 'run':
                remoteDir = os.path.join(remoteDir, "bin")

            localFileName = ''
            if scriptName == 'run':
                localFileName = 'run_%s.sh' % self.node
            elif scriptName == 'stop.sh':
                localFileName = 'stop_%s.sh' % self.node
            elif scriptName == 'restart_by_supervise.sh':
                localFileName = 'restart_%s.sh' % self.node
            else:
                localFileName = 'dummy_server_%s.port' % self.node
            
            localScriptPath = os.path.join(scriptDir, localFileName)
            if not util.execScpRemoteCommand(self.host, localScriptPath, os.path.join(remoteDir, scriptName)):
                exit(1)
        
        

    def makeRemoteDir(self):
        util.execSSHCommand(self.host, "mkdir -p %s" % self.path)
        util.execSSHCommand(self.host, "mkdir -p %s" % os.path.join(self.path, "bin"))
        util.execSSHCommand(self.host, "mkdir -p %s" % os.path.join(self.path, "conf"))
        util.execSSHCommand(self.host, "mkdir -p %s" % os.path.join(self.path, "log"))

    def removeRemoteDir(self):
        cmd = "rm -rf %s" % self.path
        util.execSSHCommand(self.host, cmd)

    def updateRemoteBin(self):
        localbin = os.path.join(REPO_DIR, self.version, "bin", BIN_NAME_DICT[self.type])
        cmd = "rm -f %s" % os.path.join(self.path, "bin", BIN_NAME_DICT[self.type] + ".tmp")
        util.execSSHCommand(self.host, cmd)
        if not util.execScpRemoteCommand(self.host, localbin, os.path.join(self.path, "bin", BIN_NAME_DICT[self.type] + ".tmp")):
            exit(1)
        cmd = "cd %s && cp -f bin/%s.tmp bin/%s" % (self.path, BIN_NAME_DICT[self.type], BIN_NAME_DICT[self.type])
        util.execSSHCommand(self.host, cmd)

    def updateRemoteConfig(self, fileName):
        if not util.execScpRemoteCommand(self.host, fileName, os.path.join(self.path, "conf", "gflags.conf")):
            exit(1) 

    def getRemoteConfig(self, fileName):
        if not util.execScpLocalCommand(self.host, fileName, os.path.join(self.path, "conf", "gflags.conf")):
            exit(1)

    def getRemoteRun(self, fileName):
        if not util.execScpLocalCommand(self.host, fileName, os.path.join(self.path, "bin", "run")):
            exit(1)

    def getRegionCount(self):
        if self.type != 'store':
            return 0
        rlist = self.storeInteract.getRegionList()
        if rlist == None:
            return 0
        return len(rlist)
        
    def transferMetaLeader(self):
        print "transferMetaLeader:"
        self.metaClient.transferMetaLeader(self.node)

    def start(self):
        if self.type == 'store' and self.check():
            self.transferAllLeader()

        if self.type == 'meta' and self.check():
            self.transferMetaLeader()
            time.sleep(10)
        cmd = "cd %s && bash restart_by_supervise.sh" % self.path
        sys.stdout.write("%s begin start!\r" % self.node)
        sys.stdout.flush()
        util.execSSHCommand(self.host, cmd)
        time.sleep(2)
        checkRet = self.check()
        if checkRet:
            print "%s start \033[1;32m succ \033[0m!" % self.node
        else:
            print "%s start \033[1;31m faild \033[0m!" % self.node
            exit(0)

    def restart(self):
        #self.stop()
        self.start()

    def getStartTime(self):
        return util.getStartTime(self.host, self.port, self.type)

    def getAliveTime(self):
        return util.getAliveTime(self.host, self.port, self.type)

    def transferAllLeader(self):
        if not self.check():
            return
        print "transfer leader", self.node
        regionList = self.storeInteract.getRegionList()
        if regionList == None:
            print "get region list faild!", self.node
            exit(1)
        for reg in regionList:
            if reg['leader'] == self.node:
                self.storeInteract.quitLeader(reg['region_id'])
        
    def stop(self):
        cmd = "cd %s && bash stop.sh" % self.path
        sys.stdout.write("stop instance %s\r" % self.node)
        sys.stdout.flush()
        util.execSSHCommand(self.host, cmd)
        time.sleep(2)
        checkRet = self.check()
        if not checkRet:
            print "%s stop \033[1;32m succ \033[0m!" % self.node
        else:
            print "%s stop \033[1;31m faild \033[0m!" % self.node
            exit(0)

    def check(self):
        return util.checkNode(self.host, self.port)

    def getIllegalRegion(self):
        if self.type != 'store':
            return None
        return self.storeInteract.getIllegalRegion()
    def getRegionList(self):
        if self.type != 'store':
            return None
        return self.storeInteract.getRegionList()
    def getRegionInfo(self, regionID):
        if self.type != 'store':
            return {}
        return self.storeInteract.getRegionInfo(regionID)

    def getRaftInfo(self, regionID):
        if self.type != 'store':
            return None
        return self.storeInteract.getRaftInfo(regionID)

    def getRaftList(self):
        if self.type != 'store':
            return None
        return self.storeInteract.getRaftList()

    def removeRegion(self, regionID):
        if self.type != 'store':
            return 
        return self.storeInteract.removeRegion(regionID)

    def removePeer(self, regionID, peer):
        if self.type != 'store':
            return
        return self.storeInteract.removePeer(regionID, peer)

    def setPeers(self, regionID, oldpeers, newpeers):
        if self.type != 'store':
            return
        return self.storeInteract.setPeers(regionID, oldpeers, newpeers)

    def forceSetPeers(self, regionID, oldpeers, newpeers):
        if self.type != 'store':
            return
        return self.storeInteract.forceSetPeers(regionID, oldpeers, newpeers)


    @staticmethod
    def getInstanceListByDeployConfig(deployConfig, module = None, node = None):
        res = []
        rootDir = deployConfig['global']['root_dir']
        clusterName = deployConfig['global']['cluster']
        moduleList = ['meta','store','db']
        version = deployConfig['global']['version']
        if module != None:
            moduleList = [module]
        metaList = []
        for ins in deployConfig['meta']:
            tmpNode = '%s:%s' % (ins['host'], ins['port'])
            metaList.append(tmpNode)
        for module in moduleList:
            for ins in deployConfig[module]:
                host = ins['host']
                port = ins['port']
                if 'path' in ins:
                    path = ins['path']
                else:
                    path = util.getDefaultPath(module, port)
                instance = Instance(host, port, clusterName, module, version, os.path.join(rootDir, path), metaList)
                if 'mem_limit' in ins:
                    instance.memLimit = ins['mem_limit']
                if 'cpu_cores' in ins:
                    instance.cpuCores = ins['cpu_cores']
                if 'config' in ins:
                    instance.config = ins['config']
                if instance.node == node:
                    return instance
                res.append(instance)
        if node != None:
            return None
        return res

