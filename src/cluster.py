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
	print "clustername\tversion\t\tmeta"
	for cluster in os.listdir(clusterDir):
	    deployConfig = DeployConfig.loadClusterDeployConfig(cluster)
	    metaList = DeployConfig.getMetaList(deployConfig)
	    version = deployConfig['global']['version']
	    wor = cluster + '\t\t' + version + '\t' + ','.join(metaList)
	    print wor
