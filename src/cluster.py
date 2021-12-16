#!/usr/bin/python
#-*- coding:utf8 -*-

import os
import sys
import yaml
import paramiko
import subprocess
from deployConfig import DeployConfig
import util
from common import CLUSTER_DIR
from tabulate import tabulate

class ClusterProcessor():
    def __init__(self):
        pass
    def usage(self):
        print "baiup cluster"

    def process(self):
        if len(sys.argv) < 2:
            self.usage()
            exit(0)
        clusterDir = CLUSTER_DIR
        rows = []
	if os.path.exists(clusterDir):
            for cluster in os.listdir(clusterDir):
                deployConfig = DeployConfig.loadClusterDeployConfig(cluster)
                metaList = DeployConfig.getMetaList(deployConfig)
                version = deployConfig['global']['version']
                wor = cluster + '\t\t\t' + version + '\t\t' + ','.join(metaList)
                rows.append([cluster, version, ','.join(metaList)])
        print tabulate(rows, headers = ['cluster','version','meta'])
