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

class ConnectProcessor():
    def __init__(self):
        pass
    def usage(self):
        print "baiup connect cluster dbname [dbnode]"

    def process(self):
        if len(sys.argv) < 3:
            self.usage()
            exit(0)
        clusterDir = CLUSTER_DIR
        self.clusterName = sys.argv[2]
        self.deployConfig = DeployConfig.loadClusterDeployConfig(self.clusterName)
        self.metaList = DeployConfig.getMetaList(self.deployConfig)
        self.metaClient = MetaClient(','.join(self.metaList))
        self.userDict = self.getUserDict()
        self.connectDatabase()

    def getUserDict(self):
        userDict = {}
        user_privileges = self.metaClient.getUserPrivileges()
        dblist = self.metaClient.getDatabases()
        dbdict = {}
        for db in dblist:
            ns = db['namespace_name']
            dbname = db['database']
            if ns not in dbdict:
                dbdict[ns] = {}
            dbdict[ns][dbname] = 1
        for user_info in user_privileges:
            namespace_name = user_info['namespace_name']
            if namespace_name not in dbdict:
                continue
            user_name = user_info['username']
            password = user_info['password']
            if 'privilege_database' not in user_info:
                continue
            for dbinfo in user_info['privilege_database']:
                dbname = dbinfo['database']
                if dbname not in dbdict[namespace_name]:
                    continue
                if dbname not in userDict:
                    userDict[dbname] = {}
                userDict[dbname][namespace_name] = {"user":user_name,"password":password}
        return userDict

    def choseDBName(self):
        dbnamelist = self.userDict.keys()
        for i in range(0, len(dbnamelist)):
            print "%d\t%s" % (i + 1, dbnamelist[i])
        
        print "请选择库名"
        dbindex = raw_input("请输入编号或库名:")
        if dbindex.isdigit():
            dbindex = int(dbindex)
            if dbindex < 1 or dbindex > len(dbnamelist):
                print "输入有误"
                exit(0)
            return dbnamelist[dbindex - 1]
        else:
            if dbindex not in dbnamelist:
                print "输入有误"
                exit(0)
            return dbindex

    def choseNamespace(self, dbname):
        namespacelist = self.userDict[dbname].keys()
        for i in range(0, len(namespacelist)):
            print "%d\t%s" % (i + 1, namespacelist[i])
        
        nsindex = raw_input("请输入编号或namespace:")
        print "[%s]" % nsindex
        if nsindex.isdigit():
            nsindex = int(nsindex)
            if nsindex < 1 or nsindex > len(namespacelist):
                print "输入有误"
                exit(0)
            return namespacelist[nsindex - 1]
        else:
            if nsindex not in namespacelist:
                print "输入有误"
                exit(0)
            return nsindex
        
        
                
    def connectDatabase(self):
        dbname = ''
        if len(sys.argv) >= 4:
            dbname = sys.argv[3]
        dbnode = ''
        if len(sys.argv) == 5:
            dbnode = sys.argv[4]
        if dbname == '':
            dbname = self.choseDBName()

        if dbname not in self.userDict:
            print "不存在的库名"
            exit(0)
        namespace = ''
        if len(self.userDict[dbname]) > 1:
            namespace = self.choseNamespace(dbname)
        else:
            namespace = self.userDict[dbname].keys()[0]
         
        if dbnode == '':
            dbnode = self.deployConfig['db'][0]
            dbnode = dbnode['host']  + ':' + str(dbnode['port'])

        host = dbnode.split(':')[0]
        port = dbnode.split(':')[1]

        cmd = 'mysql -h%s -P%s -u%s -p%s -D%s' % (host, port, self.userDict[dbname][namespace]['user'], self.userDict[dbname][namespace]['password'], dbname)
        os.system(cmd)
