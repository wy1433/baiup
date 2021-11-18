#!/usr/bin/python
#-*- coding:utf8 -*-

import os
import sys
import yaml
import json
import paramiko
import subprocess
from deployConfig import DeployConfig
import util
from common import CLUSTER_DIR
from instance import Instance
from metaClient import MetaClient
from tabulate import tabulate

class RegionProcessor():
    def __init__(self):
        pass
    def usage(self):
        print "baiup region cluster illegal|remove-illegal|count|diff|applying|peer-count"

    def process(self):
        if len(sys.argv) < 3:
            self.usage()
            exit(0)
        clusterDir = CLUSTER_DIR
        self.clusterName = sys.argv[2]
        self.deployConfig = DeployConfig.loadClusterDeployConfig(self.clusterName)
        self.metaList = DeployConfig.getMetaList(self.deployConfig)
        self.metaClient = MetaClient(','.join(self.metaList))
        self.cmd = ''
        if len(sys.argv) >= 4:
            self.cmd = sys.argv[3]
        if self.cmd == 'list':
            self.showRegionList()
        elif self.cmd == 'illegal':
            self.queryIllegalRegion()
        elif self.cmd == 'remove-illegal':
            self.removeIllegalRegion()
        elif self.cmd == 'count':
            self.showRegionCount()
        elif self.cmd == 'diff':
            self.showDiffRegions()
        elif self.cmd == 'noleader':
            self.showNoLeaderRegions()
        elif self.cmd == 'info':
            self.showRegionInfo()
        elif self.cmd == 'raftinfo':
            self.showRaftInfo()
        elif self.cmd == "raftlist":
            self.showRaftList()
        elif self.cmd == 'remove-peer':
            self.removePeer()
        elif self.cmd == 'add-peer':
            self.addPeer()
        elif self.cmd == 'applying':
            self.showApplyingCount()
        elif self.cmd.startswith('peer-count'):
            self.showPeerCount()
        else:
            self.usage()
            exit(0)

    def showRegionCount(self):
        regionList = self.metaClient.getRegionInfo()
        allcount = len(regionList)
        storeRegionDict = {}
        for reg in regionList:
            rid = reg['region_id']
            leader = reg['leader']
            if leader not in storeRegionDict:
                storeRegionDict[leader] = {'leader':0, 'count':0}
            storeRegionDict[leader]['leader'] += 1
            for peer in reg['peers']:
                if peer not in storeRegionDict:
                    storeRegionDict[peer] = {'leader':0, 'count':0}
                storeRegionDict[peer]['count'] += 1

        print "store\t\t\t\tleader\t\tcount"
        for store, item in storeRegionDict.items():
             print "%s\t\t%d\t\t%d" % (store, item['leader'], item['count'])


    def showDiffRegions(self):
        self.node = ''
        metaRegionList = self.metaClient.getRegionInfo()
        metaRegionDict = {}
        for reg in metaRegionList:
            rid = reg['region_id']
            metaRegionDict[rid] = reg
        self.node = ''
        self.resource_tag = None
        if len(sys.argv) >= 5:
            if sys.argv[4].startswith('resource_tag='):
                self.resource_tag = sys.argv[4][13:].strip()
            else:
                self.node = sys.argv[4]

        instanceList = []
        if self.node == '':
            tmpInstanceList = Instance.getInstanceListByDeployConfig(self.deployConfig, "store")
            for instance in tmpInstanceList:
                if self.resource_tag != None:
                    if '-resource_tag' not in instance.config:
                        continue
                    if instance.config['-resource_tag'] != self.resource_tag:
                        continue
                instanceList.append(instance)
        else:
            instance = Instance.getInstanceListByDeployConfig(self.deployConfig, node = self.node)
            if instance == None:
                print "has not node :%s" % self.node
                return
            instanceList.append(instance)
        for instance in instanceList:
            if instance.check() == False:
                continue
            regionList = instance.getRegionList()
            for reg in regionList:
                rid = reg['region_id']
                metaLeader = "None"
                leader = reg['leader']
                if rid in metaRegionDict:
                    metaLeader = metaRegionDict[rid]['leader']
                if leader != metaLeader:
                    print "%s\t%d\t%s\t%s" % (instance.node, rid, leader, metaLeader)
        
    def showRaftInfo(self):
        if len(sys.argv) < 6:
            print "usage: baiup region cluster raftinfo storeid region_id"
            return
        self.node = sys.argv[4]
        region_id = int(sys.argv[5])
        
        instance = Instance.getInstanceListByDeployConfig(self.deployConfig, node = self.node)
        if instance == None:
            print "has not node :%s" % self.node
            return
        print instance.getRaftInfo(region_id)

    def showApplyingCount(self):
        self.node = ''
        self.resource_tag = None
        if len(sys.argv) == 5:
            if sys.argv[4].startswith('resource_tag='):
                self.resource_tag = sys.argv[4][13:].strip()
            else:
                self.node = sys.argv[4]
        instanceList = Instance.getInstanceListByDeployConfig(self.deployConfig, "store")
        rows = []
        for instance in instanceList:
            if self.node != '' and self.node != instance.node:
                continue
            if self.resource_tag != None:
                if '-resource_tag' not in instance.config:
                    continue
                if instance.config['-resource_tag'] != self.resource_tag:
                    continue
            raftList = instance.getRaftList()
            if raftList == None:
                rows.append([instance.node, "DOWN"])
                continue
            count = 0
            for raft in raftList:
                if raft.find("state_machine: Applying") != -1:
                    count += 1
            rows.append([instance.node, count])
        print tabulate(rows, headers = ['instance', 'applying-count'])
            
        
    def showRaftList(self):
        if len(sys.argv) != 5:
            print "usage: baiup region cluster raftlist storeid"
            return
        self.node = sys.argv[4]
        instance = Instance.getInstanceListByDeployConfig(self.deployConfig, node = self.node)
        if instance == None:
            print "has not node :%s" % self.node
            return
        raftList = instance.getRaftList()
        for raftInfo in raftList:
            if raftInfo.strip() == '':
                continue
            print "###############################"
            print raftInfo
        
        

    def showRegionList(self):
        self.node = ''
        self.resource_tag = None
        self.db = None
        if len(sys.argv) == 5:
            if sys.argv[4].startswith('resource_tag='):
                self.resource_tag = sys.argv[4][13:].strip()
            elif sys.argv[4].startswith('db='):
                self.db = sys.argv[4][3:]
            else:
                self.node = sys.argv[4]

        rows = []
        metaRegionPeers = {}
        metaRegionList = self.metaClient.getRegionInfo()
        region2table = {}
        for reg in metaRegionList:
            metaRegionPeers[reg['region_id']] = reg['peers']
            table_id = reg['table_id']
            region2table[reg['region_id']] = table_id
        if self.node == '' and self.resource_tag == None:
            for reg in metaRegionList:
                rows.append([reg['region_id'], reg['leader'], reg['peers']])
        else:
            instanceList = Instance.getInstanceListByDeployConfig(self.deployConfig)
            for instance in instanceList:
                if self.node != '' and instance.node != self.node:
                    continue
                if self.resource_tag != None:
                    if '-resource_tag' not in instance.config:
                        continue
                    if instance.config['-resource_tag'] != self.resource_tag:
                        continue
                regionList = instance.getRegionList()
                for reg in regionList:
                    peers = 'None'
                    if reg['region_id'] in metaRegionPeers:
                        peers = json.dumps(metaRegionPeers[reg['region_id']])
                    rows.append([reg['region_id'], reg['leader'],peers])
        #根据db过滤
        if self.db != None:
            tableList = self.metaClient.getTableListByDatabase(self.db)
            tableIDDict = {}
            for table in tableList:
                table_id = table['table_id']
                tableIDDict[table_id] = 1
            newrows = []        
            for row in rows:
                rid = row[0]
                tid = region2table[rid]
                if tid in tableIDDict:
                    newrows.append(row)
            rows = newrows
        
        print tabulate(rows, headers = ['region_id','leader','peers'])
            

    def showRegionInfo(self):
        if len(sys.argv) < 5:
            print "usage : baiup region cluster info region_id [store]"
            return
        region_id = int(sys.argv[4])
        self.node = ''
        if len(sys.argv) > 5:
            self.node = sys.argv[5]
        if self.node != '':
            for instance in Instance.getInstanceListByDeployConfig(self.deployConfig, 'store'):
                if instance.node != self.node:
                    continue
                regionInfo = instance.getRegionInfo(region_id)
                print "store region info"
                print json.dumps(regionInfo, ensure_ascii=False, indent = 4)
            return
            
        metaRegionList = self.metaClient.getRegionInfo()
        regionInfo = {}
        for reg in metaRegionList:
            if reg['region_id'] == region_id:
                regionInfo = reg
        print json.dumps(regionInfo, ensure_ascii=False, indent = 4)

    def showNoLeaderRegions(self):
        self.node = ''
        self.resource_tag = None
        if len(sys.argv) == 5:
            if sys.argv[4].startswith('resource_tag='):
                self.resource_tag = sys.argv[4][13:]
            else:
                self.node = sys.argv[4]
        metaRegionList = self.metaClient.getRegionInfo()
        metaRegionDict = {}
        instanceStatus = self.metaClient.getInstanceStatusList()
        for instance in Instance.getInstanceListByDeployConfig(self.deployConfig, 'store'):
            if instance.check() == False:
                instanceStatus[instance.node] = "DOWN"
        for reg in metaRegionList:
            rid = reg['region_id']
            metaRegionDict[rid] = reg
        for instance in Instance.getInstanceListByDeployConfig(self.deployConfig, 'store'):
            if instance == None or instance.check() == False:
                continue
            if self.node != '' and self.node != instance.node:
                continue
            if self.resource_tag != None:
                if '-resource_tag' not in instance.config:
                    continue
                if instance.config['-resource_tag'] != self.resource_tag:
                    continue
            regionList = instance.getRegionList()
            for region in regionList:
                if region['leader'] == '0.0.0.0:0':
                    peers = 'None'
                    wor = "%d\t%s\t" % (region['region_id'], instance.node)
                    if region['region_id'] in metaRegionDict:
                        peersPrint = []
                        for peer in metaRegionDict[region['region_id']]['peers']:
                            if peer in instanceStatus and instanceStatus[peer] == 'DOWN':
                                a = "\033[1;31m%s\033[0m" % peer
                            else:
                                a = peer
                            peersPrint.append(a)
                        peers = ','.join(peersPrint)
                    wor += peers
                    print wor



    def queryIllegalRegion(self):
        self.node = ''
        if len(sys.argv) == 5:
            self.node = sys.argv[4]

        regionInfos = self.metaClient.getRegionInfo()
        self.regionDict = {}
        for reg in regionInfos:
            rid = reg['region_id']
            self.regionDict[rid] = reg
        for instance in Instance.getInstanceListByDeployConfig(self.deployConfig, 'store'):
            if self.node != '' and self.node != instance.node:
                continue

            illegalRegion = instance.getIllegalRegion()
            if illegalRegion == None:
                print instance.node, " is down!"
                continue
            for reg in illegalRegion:
                peers = 'None'
                rid = reg['region_id']
                if rid in self.regionDict:
                    peers = self.regionDict[rid]['peers']
                    peers = ','.join(peers)
                    print instance.node + '\t' + str(reg['region_id']) + '\t' + peers

    def showPeerCount(self):
        self.node = ''
        self.resource_tag = None
        if len(sys.argv) == 5:
            if sys.argv[4].startswith('resource_tag='):
                self.resource_tag = sys.argv[4][13:]
            else:
                self.node = sys.argv[4]
        requirePeerCount = -1
        if self.cmd.find('=') != -1:
            requirePeerCount = int(self.cmd.split('=')[-1])
        nodeDict = {}
        instanceList = Instance.getInstanceListByDeployConfig(self.deployConfig)
        for instance in instanceList:
            if self.node != '' and instance.node != self.node:
                continue
            if self.resource_tag != None:
                if '-resource_tag' not in instance.config:
                    continue
                if instance.config['-resource_tag'] != self.resource_tag:
                    continue
            nodeDict[instance.node] = 1
        regionList = self.metaClient.getRegionInfo()
        rows = []
        for reg in regionList:
            peerCnt = len(reg['peers'])
            if requirePeerCount != -1 and requirePeerCount != peerCnt:
                continue
            rid = reg['region_id']
            leader = reg['leader']
            if leader not in nodeDict:
                continue
            rows.append([rid, peerCnt, leader, json.dumps(reg['peers'])])

        print tabulate(rows, headers = ['region_id', 'peer_count', 'leader','peers'])
        


    def removeIllegalRegion(self):
        self.node = ''
        if len(sys.argv) == 5:
            self.node = sys.argv[4]

        regionInfos = self.metaClient.getRegionInfo()
        self.regionDict = {}
        for reg in regionInfos:
            rid = reg['region_id']
            self.regionDict[rid] = reg
        for instance in Instance.getInstanceListByDeployConfig(self.deployConfig, 'store'):
            if self.node != '' and self.node != instance.node:
                continue

            illegalRegion = instance.getIllegalRegion()
            for reg in illegalRegion:
                peers = []
                rid = reg['region_id']
                if rid in self.regionDict:
                    peers = self.regionDict[rid]['peers']
                if self.node not in peers:
                    print "remove region %s in %s" % (rid, instance.node)
                    instance.removeRegion(rid)

    def removePeer(self):
        if len(sys.argv) != 6:
            print "usage: baiup region cluster remove-peer regionid peerid"
            return
        region_id = int(sys.argv[4])
        peerid = sys.argv[5]
        
        metaRegionList = self.metaClient.getRegionInfo()
        regionInfo = {}
        for reg in metaRegionList:
            if reg['region_id'] == region_id:
                regionInfo = reg

        if regionInfo == {}:
            print "has no region %d" % region_id
            return
        if peerid not in regionInfo['peers']:
            print "region %d has not peer %s" % (region_id, peerid)
            return

        if len(regionInfo['peers']) == 1:
            print "region %d has only on peer, cant remove" % region_id
            return

        leader = regionInfo['leader']
        oldpeerslist = regionInfo['peers']
        newpeerslist = []
        for peer in oldpeerslist:
            if peer != peerid:
                newpeerslist.append(peer)
        if len(newpeerslist) == len(oldpeerslist):
            print "has no peer to remove"
            return
        #从store获取leader
        #for peer in newpeerslist: 
        #    instance = Instance.getInstanceListByDeployConfig(self.deployConfig, node = peer)
        #    if instance == None or instance.check() == False:
        #        print "peer %s not exist or dead!" % peer
        #        continue
        #    storeRegionInfo = instance.getRegionInfo(region_id)
        #    if storeRegionInfo == None:
        #        print "store get region info faild! store:%s" % peer
        #        continue
        #    res = instance.forceSetPeers(region_id, oldpeerslist, newpeerslist)
        #    if res:
        #        print "store %s region %d remove peer %s success!" % (peer, region_id, peerid)
        #    else:
        #        print "remove peer faild! region :%d, store: %s, remove-peer: %s" % (region_id, peer, peerid)
        #return

        if leader == '0.0.0.0:0:0':
            #没有主节点，需要force set peer
            for peer in newpeerslist:
                instance = Instance.getInstanceListByDeployConfig(self.deployConfig, node = peer)
                if instance == None or instance.check() == False:
                    print "peer % not exist or dead!" % peer
                    continue
                res = instance.forceSetPeers(region_id, oldpeerslist, newpeerslist)
                if res :
                    print "store %s region %d remove peer %s success!" % (peer, region_id, peerid)
                else:
                    print "remove peer faild! region :%d, store: %s, remove-peer: %s" % (region_id, peer, peerid)
            return
                
        instance = Instance.getInstanceListByDeployConfig(self.deployConfig, node = leader)
        if instance == None or not instance.check():
            print "has no leader %s or store down" % leader
            return
        if leader == peerid:
            instane.transferLeader(regionID)
            leader = instance.getLeader(regionID)
            
        res = instance.setPeers(region_id, oldpeerslist, newpeerslist)
        if res:
            print "region %d remove peer %s success!" % (region_id, peerid)
        else:
            print "region %d remove peer %s faild!" % (region_id, peerid)

    def addPeer(self):
        if len(sys.argv) != 6:
            print "usage: baiup region cluster add-peer regionid peerid"
            return
        region_id = int(sys.argv[4])
        peerid = sys.argv[5]
        
        metaRegionList = self.metaClient.getRegionInfo()
        regionInfo = {}
        for reg in metaRegionList:
            if reg['region_id'] == region_id:
                regionInfo = reg

        if regionInfo == {}:
            print "has no region %d" % region_id
            return
        if peerid  in regionInfo['peers']:
            print "region %d already has peer %s" % (region_id, peerid)
            return

        leader = regionInfo['leader']
        instance = Instance.getInstanceListByDeployConfig(self.deployConfig, node = leader)
        if instance == None:
            print "has not store %s" % leader
            return
        oldpeerslist = regionInfo['peers']
        newpeerslist = []
        for peer in oldpeerslist:
            newpeerslist.append(peer)
        newpeerslist.append(peerid)
        res = instance.setPeers(region_id, oldpeerslist, newpeerslist)
        if res:
            print "region %d add peer %s success!" % (region_id, peerid)
        else:
            print "region %d add peer %s faild!" % (region_id, peerid)
