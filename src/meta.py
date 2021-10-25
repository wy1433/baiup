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
	logicalRoomList = self.metaClient.getLogicalRoom()
	for logicalRoom in logicalRoomList:
	    logicalRoomName = logicalRoom['logical_room']
	    if 'physical_rooms' not in logicalRoom:
		continue
	    for physical in logicalRoom['physical_rooms']:
		print "%s\t%s" % (logicalRoomName, physical)

    def queryPhysicalRoom(self):
	for physicalInstance in self.metaClient.getPhysicalRoom():
	    logical_room = physicalInstance['logical_room']
	    physical_room = physicalInstance['physical_room']
	    if 'instances' not in physicalInstance:
		continue
	    for instance in physicalInstance['instances']:
		print "%s\t%s\t%s" % (logical_room, physical_room, instance)
