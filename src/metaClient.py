#!/usr/bin/python
#-*- coding:utf8 -*-
# 从meta获取table，region信息 #

import urllib
import urllib2
import time
import traceback
import json

class MetaClient:
    def __init__(self, addrList):
        self.addrList = addrList.split(',')
        self.leader = self.addrList[0]
        self.addrIndex = 0
        self.tableSchemaQuery = '{"op_type" : "QUERY_SCHEMA"}'
        self.regionQuery = '{"op_type" : "QUERY_REGION"}'
        self.getLeaderQuery = '{"op_type" : "GetLeader","region_id":0}'

    def getLeader(self):
        res = None
        for addr in self.addrList:
            url = 'http://%s/%s' % (addr, 'MetaService/raft_control')
            try:
                req = urllib2.Request(url, self.getLeaderQuery)
                response = urllib2.urlopen(req)
                res = response.read()
                break
            except Exception,e:
                print str(e)
                continue
        if res == None:
            return None
        try:
            jsres = json.loads(res)
            leader = jsres['leader']
            return leader
        except Exception,e:
            print traceback.format_exc()
            return None
            

    def getInstanceStatus(self, instance):
        instanceStatusQuery = '{"op_type" : "QUERY_INSTANCE","instance_address" : "%s"}' % instance
        res, errMsg = self.post('/MetaService/query', instanceStatusQuery)
        try:
            jsres = json.loads(res)
            if 'instance_infos' not in jsres:
                return "NOINS"
            for ins in jsres['instance_infos']:
                if ins['address'] == instance:
                    return ins['status']
            return None
        except Exception,e:
            return None

    def getInstanceRegionCount(self, instance):
        instanceStatusQuery = '{"op_type" : "QUERY_INSTANCE","instance_address" : "%s"}' % instance
        res, errMsg = self.post('/MetaService/query', instanceStatusQuery)
        try:
            jsres = json.loads(res)
            cnt = 0
            if 'region_infos' in jsres:
                cnt = len(jsres['region_infos'])
            return cnt
        except Exception,e:
            return None

    def getInstanceList(self):
        instanceStatusQuery = '{"op_type" : "QUERY_INSTANCE"}'
        res, errMsg = self.post('/MetaService/query', instanceStatusQuery)
        try:
            jsres = json.loads(res)
            cnt = 0
            insList = []
            for instance in jsres['instance_infos']:
                insList.append(instance['address'])
            return insList
        except Exception,e:
            return []
        

    def setInstanceMigrate(self, instance):
        setMigrateQuery = '{"op_type": "OP_SET_INSTANCE_MIGRATE","instance": {"address" : "%s"}}' % instance
        res, errMsg = self.post('/MetaService/meta_manager', setMigrateQuery)
        try:
            jsres = json.loads(res)
            return jsres['errcode'] == 'SUCCESS'
        except Exception,e:
            return False
        return False
        
    def dropInstance(self, instance):
        setMigrateQuery = '{"op_type": "OP_DROP_INSTANCE","instance": {"address" : "%s"}}' % instance
        res, errMsg = self.post('/MetaService/meta_manager', setMigrateQuery)
        try:
            jsres = json.loads(res)
            return jsres['errcode'] == 'SUCCESS'
        except Exception,e:
            return False
        return False
        

    def getTableSchema(self):
        res, errMsg = self.post('/MetaService/query', self.tableSchemaQuery)
        try:
            jsres = json.loads(res)
            if 'schema_infos' not in jsres:
                return []
            return jsres['schema_infos']
        except Exception,e:
            print traceback.format_exc()
            return []


    def getRegionInfo(self):
        res, errMsg = self.post('/MetaService/query', self.regionQuery)
        try:
            jsres = json.loads(res)
            if 'region_infos' not in jsres:
                return []
            return jsres['region_infos']
        except Exception,e:
            print traceback.format_exc()
            return []

                

    def post(self,uri,data):
        res = None
        tryTimes = 3
        errorMsg = ''
        while tryTimes:
            tryTimes -= 1
            try:
                url = 'http://%s/%s' % (self.getLeader(), uri)
                req = urllib2.Request(url, data)
                response = urllib2.urlopen(req)
                res = response.read()
            except Exception,e:
                time.sleep(1)
                continue
            break
        if res == None:
            print traceback.format_exc()
            return res, errorMsg
        return res,''


if __name__ == '__main__':
    meta = MetaClient('10.100.217.149:9010,10.100.217.150:9010')
    print meta.getInstanceRegionCount('10.100.217.149:8116')
