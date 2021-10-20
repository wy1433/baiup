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

class RegionProcessor():
    def __init__(self):
        pass
    def usage(self):
        print "baiup region cluster illegal|remove-illegal|count|diff"

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
	if self.cmd == '':
	    self.showRegionList()
	elif self.cmd == 'list':
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
	else:
	    self.usage()
	    exit(0)

    def showRegionCount(self):
	self.node = ''
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
	self.node = ''
	if len(sys.argv) >= 5:
	    self.node = sys.argv[4]

	instanceList = []
	if self.node == '':
	    instanceList = Instance.getInstanceListByDeployConfig(self.deployConfig, "store")
	else:
	    instance = Instance.getInstanceListByDeployConfig(self.deployConfig, node = self.node)
	    instanceList.append(instance)
	for instance in instanceList:
	    pass
	
	
    def showRaftInfo(self):
	if len(sys.argv) < 6:
	    print "usage: baiup region cluster raftinfo storeid region_id"
	self.node = sys.argv[4]
	region_id = int(sys.argv[5])
	
	instance = Instance.getInstanceListByDeployConfig(self.deployConfig, node = self.node)
	print instance.getRaftInfo(region_id)
	
    def showRaftList(self):
	if len(sys.argv) != 5:
	    print "usage: baiup region cluster raftlist storeid"
	self.node = sys.argv[4]
	instance = Instance.getInstanceListByDeployConfig(self.deployConfig, node = self.node)
	raftList = instance.getRaftList()
	for raftInfo in raftList:
	    if raftInfo.strip() == '':
		continue
	    print "###############################"
	    print raftInfo
	
	

    def showRegionList(self):
	self.node = ''
	if len(sys.argv) == 5:
	    self.node = sys.argv[4]

	if self.node == '':
	    regionList = self.metaClient.getRegionInfo()
	
	    for reg in regionList:
	        print reg['region_id'], reg['leader'], reg['peers']
	else:
	    if True:
		instance = Instance.getInstanceListByDeployConfig(self.deployConfig, node = self.node)
		regionList = instance.getRegionList()
		for reg in regionList:
		    print reg['region_id'], reg['leader']
	    

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
	if len(sys.argv) == 5:
	   self.node = sys.argv[4]
	metaRegionList = self.metaClient.getRegionInfo()
	metaRegionDict = {}
	for reg in metaRegionList:
	    rid = reg['region_id']
	    metaRegionDict[rid] = reg
	for instance in Instance.getInstanceListByDeployConfig(self.deployConfig, 'store'):
	    if self.node != '' and self.node != instance.node:
		continue

	    regionList = instance.getRegionList()
	    for region in regionList:
		if region['leader'] == '0.0.0.0:0':
		    peers = 'None'
		    if region['region_id'] in metaRegionDict:
			peers = ','.join(metaRegionDict[region['region_id']]['peers'])
		    print region['region_id'], instance.node, peers



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
	    for reg in illegalRegion:
		peers = 'None'
		rid = reg['region_id']
		if rid in self.regionDict:
		    peers = self.regionDict[rid]['peers']
		    peers = ','.join(peers)
	    	print instance.node + '\t' + str(reg['region_id']) + '\t' + peers

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
	instance = Instance.getInstanceListByDeployConfig(self.deployConfig, node = leader)
	if leader == peerid:
	    instane.transferLeader(regionID)
	    leader = instance.getLeader(regionID)
	    
	oldpeerslist = regionInfo['peers']
	newpeerslist = []
	for peer in oldpeerslist:
	    if peer == peerid:
		continue
	    newpeerslist.append(peer)
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
