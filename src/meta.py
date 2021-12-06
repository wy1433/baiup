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
        print "baiup meta cluster close-balance|open-balance|logical|physical|instance|transfer-leader|get-leader|table"

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
	elif self.cmd == "transfer-leader":
	    self.transferLeader()
	elif self.cmd == "get-leader":
	    self.getLeader()
	elif self.cmd == "table":
	    self.getTables()
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
    def transferLeader(self):
	if len(sys.argv) != 5:
	    print "usage: baiup meta cluster transfer-leader ip:port"
	    return
	instance = sys.argv[4]
	self.metaClient.transferMetaLeader(instance)
        print "transfer-leader %s success" % instance

    def getLeader(self):
	leaders = self.metaClient.getLeader()
        rows = []
	for region_id in (0,1,2):
	    leader = self.metaClient.getLeader(region_id)
	    rows.append([region_id, leader])
	print tabulate(rows, headers = ['region_id','leader'])
    def getTables(self):
	tableList = self.metaClient.getTableSchema()
	table_id = ''
	if len(sys.argv) == 5:
	    table_id = int(sys.argv[4])
	if table_id == '':
	    rows = []
	    for table in tableList:
	        rows.append([table['namespace_name'], table['database'], table['table_name'], table['table_id']])

            print tabulate(rows, headers = ['namespace','database','table','table_id'])
	else:
	    for table in tableList:
		if table['table_id'] != table_id:
		    continue
		print json.dumps(table, indent = 4)
		break
