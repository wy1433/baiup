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

class MetaProcessor():
    def __init__(self):
        pass
    def usage(self):
        print "baiup meta cluster close-balance|open-balance|logical|physical|instance"

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
            self.usage()
        elif self.cmd == 'close-balance':
            self.closeBalance()
        elif self.cmd == 'open-balance':
            self.openBalance()
        elif self.cmd == "logical":
            self.queryLogicalRoom()
        elif self.cmd == "physical":
            self.queryPhysicalRoom()
        elif self.cmd == "instance":
            self.queryInstance()
        else:
            self.usage()
            exit(0)

    def closeBalance(self):
        if self.metaClient.closeBalance():
            print "close meta balance success!"
        else:
            print "close meta balance faild!"

    def openBalance(self):
        if self.metaClient.openBalance():
            print "open meta balance success!"
        else:
            print "open meta balance faild!"

    def queryLogicalRoom(self):
        queryLogical = ''
        if len(sys.argv) == 5:
            queryLogical = sys.argv[4]
        logicalRoomList = self.metaClient.getLogicalRoom(queryLogical)
	rows = []
        for logicalRoom in logicalRoomList:
            logicalRoomName = logicalRoom['logical_room']
            if 'physical_rooms' not in logicalRoom:
		rows.append([logicalRoomName, ''])
                continue
            for physical in logicalRoom['physical_rooms']:
		rows.append([logicalRoomName, physical])
	print tabulate(rows, headers = ['logical_room','physical_room'])

    def queryPhysicalRoom(self):
        queryPhysical = ''
        if len(sys.argv) == 5:
            queryPhysical = sys.argv[4]
	rows = []
        for physicalInstance in self.metaClient.getPhysicalRoom(queryPhysical):
            logical_room = physicalInstance['logical_room']
            physical_room = physicalInstance['physical_room']
            if 'instances' not in physicalInstance:
		cols = [logical_room, physical_room, '']
		rows.append(cols)
		continue
            for instance in physicalInstance['instances']:
		cols = [logical_room, physical_room, instance]
		rows.append(cols)
	print tabulate(rows, headers = ['logical_room','physical_room','instance'])

    def queryInstance(self):
	instance = ''
	resource_tag = None
	if len(sys.argv) == 5:
	    if sys.argv[4].startswith('resource_tag='):
		resource_tag = sys.argv[4][13:].strip()
	    else:
	        instance = sys.argv[4]
	rows = []
	for ins in self.metaClient.getInstanceInfoList(instance): 
	    if instance != '' and ins['address'] != instance:
		continue
	    if resource_tag != None and ins['resource_tag'] != resource_tag:
		continue
	    cols = [ins['address'], ins['resource_tag'], ins['status'], ins['leader_count'], ins['region_count']]
	    rows.append(cols)
	print tabulate(rows, headers = ['address','resource_tag','status','leader_count','region_count'])
