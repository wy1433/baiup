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

class StoreProcessor():
    def __init__(self):
        pass
    def usage(self):
        print "baiup store cluster transfer-leader|"

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
        elif self.cmd == 'transfer-leader':
            self.transferLeader()
        else:
            self.usage()
            exit(0)

    def transferLeader(self):
        if len(sys.argv) != 5:
            print "usage baiup store clustername transfer-leader store_id"
            exit(0)
        self.node = ''
        self.node = sys.argv[4]

        for instance in Instance.getInstanceListByDeployConfig(self.deployConfig, "store"):
            if self.node != '' and instance.node != self.node:
                continue
            instance.transferAllLeader()
            
