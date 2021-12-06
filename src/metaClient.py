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
        self.getLeaderQuery = '{"op_type" : "GetLeader","region_id":%s}'
        self.closeBalanceQuery = '{"op_type": "OP_CLOSE_LOAD_BALANCE"}'
        self.openBalanceQuery = '{"op_type": "OP_OPEN_LOAD_BALANCE"}'

    def getLeader(self, rid = 0):
        res = None
        metaLeaderQuery = self.getLeaderQuery % rid
        for addr in self.addrList:
            url = 'http://%s/%s' % (addr, 'MetaService/raft_control')
            try:
                req = urllib2.Request(url, metaLeaderQuery)
                response = urllib2.urlopen(req, timeout = 2)
                res = response.read()
                break
            except Exception,e:
                continue
        if res == None:
            return None
        try:
            jsres = json.loads(res)
            leader = jsres['leader']
            return leader
        except Exception,e:
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

    def getInstanceInfoList(self, instance):
        instanceQuery = '{"op_type": "QUERY_INSTANCE"}'
        if instance != '':
            instanceQuery = '{"op_type": "QUERY_INSTANCE", "instance_address":"%s"}' % instance
        res, errMsg = self.post('/MetaService/query', instanceQuery)
        try:
            jsres = json.loads(res)
            insList = []
            leaderCountDict = {}
            regionCountDict = {}
            for region in jsres['region_infos']:
                leader = region['leader']
                if leader not in leaderCountDict:
                    leaderCountDict[leader] = 0
                leaderCountDict[leader] += 1
                for peer in region['peers']:
                    if peer not in regionCountDict:
                        regionCountDict[peer] = 1
                    else:
                        regionCountDict[peer] += 1
            for instance in jsres['instance_infos']:
                addr = instance['address']
                regionCount = 0
                if addr in regionCountDict:
                    regionCount = regionCountDict[addr]
                leaderCount = 0
                if addr in leaderCountDict:
                    leaderCount = leaderCountDict[addr]
                ins = {
                    'address': addr,
                    'status': instance['status'],
                    'resource_tag': instance['resource_tag'],
                    'region_count': regionCount,
                    'leader_count': leaderCount
                }
                insList.append(ins)
            return insList
        except Exception,e:
            return []

    def getInstanceStatusList(self):
        instanceList = self.getInstanceList()
        res = {}
        for instance in instanceList:
            status = self.getInstanceStatus(instance)
            res[instance] = status
        return res
                


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
            return []

    def getTableListByDatabase(self, dbname):
        tableList = self.getTableSchema()
        res = []
        for table in tableList:
            if table['database'] != dbname:
                continue
            res.append(table)
        return res


    def addLogicalRoom(self, logicalRoomList):
	data = '''{
	    "op_type": "OP_ADD_LOGICAL",
	    "logical_rooms": {
		"logical_rooms" : %s
	    }
	}''' % json.dumps(logicalRoomList, ensure_ascii = False)
	res, errMsg = self.post('/MetaService/meta_manager', data)
        try:
            jsres = json.loads(res)
	    return jsres['errcode'] == 'SUCCESS'
        except Exception,e:
            return False

    def addPhysicalRoom(self, logicalRoom, physicalRoomList):
	data = '''{
	    "op_type": "OP_ADD_PHYSICAL",
	    "physical_rooms": {
		"logical_room" : "%s",
		"physical_rooms": %s
	    }
	}''' % (logicalRoom, json.dumps(physicalRoomList, ensure_ascii = False))
	res, errMsg = self.post('/MetaService/meta_manager', data)
        try:
            jsres = json.loads(res)
	    return jsres['errcode'] == 'SUCCESS'
        except Exception,e:
            return False
	
	
        
    def transferMetaLeader(self, oldLeader):
        for rid in (0,1,2):
            leader = self.getLeader(rid)
            if leader != oldLeader:
                continue
            for ins in self.addrList:
                if ins != leader:
                    transferLeaderQuery = '{"op_type" : "TransLeader","region_id" : %d,"new_leader" : "%s"}' % (rid, ins)
                    self.post('/MetaService/raft_control', transferLeaderQuery, rid)
                    break

            


    def getRegionInfo(self):
        res, errMsg = self.post('/MetaService/query', self.regionQuery)
        try:
            jsres = json.loads(res)
            if 'region_infos' not in jsres:
                return []
            return jsres['region_infos']
        except Exception,e:
            return []

                
    def closeBalance(self):
        res, errMsg = self.post("/MetaService/meta_manager", self.closeBalanceQuery)
        try:
            jsres = json.loads(res)
            print jsres
            return jsres['errcode'] == "SUCCESS"
        except Exception,e:
            print traceback.format_exc()
            return False
            
    def openBalance(self):
        res, errMsg = self.post("/MetaService/meta_manager", self.openBalanceQuery)
        try:
            jsres = json.loads(res)
            return jsres['errcode'] == "SUCCESS"
        except Exception,e:
            print traceback.format_exc()
            return False

    def getLogicalRoom(self, logicalRoom):
        data = '{"op_type":"QUERY_LOGICAL"}'
        if logicalRoom != '':
            data = '{"op_type":"QUERY_LOGICAL", "logical_room":"%s"}' % logicalRoom
        res, errMsg = self.post("/MetaService/query",data)
        try:
            jsres = json.loads(res)
            if 'physical_rooms' not in jsres:
                return []
            return jsres['physical_rooms']
        except Exception,e:
            return []

    def getDatabases(self):
        data = '{"op_type" : "QUERY_DATABASE"}'
        res, errMsg = self.post("/MetaService/query", data)
        try:
            jsres = json.loads(res)
            if 'database_infos' not in jsres:
                return []
            return jsres['database_infos']
        except Exception,e:
            return []
            
    def getPhysicalRoom(self, physicalRoom):
        data = '{"op_type":"QUERY_PHYSICAL"}'
        if physicalRoom != '':
            data = '{"op_type":"QUERY_PHYSICAL","physical_room":"%s"}' % physicalRoom
        res, errMsg = self.post("/MetaService/query",data)
        try:
            jsres = json.loads(res)
            if 'physical_instances' not in jsres:
                return []
            return jsres["physical_instances"]
        except Exception,e:
            return []

    def createNamespace(self, ns):
	data = '{"op_type":"OP_CREATE_NAMESPACE","namespace_info":{"namespace_name": "%s","quota": 1048576}}' % ns
	res, errMsg = self.post("MetaService/meta_manager", data)
	try:
	    jsres = json.loads(res)
	    return jsres['errcode'] == 'SUCCESS'
	except Exception, e:
	    return False

    def createDatabase(self, ns, db):
	data = '{"op_type":"OP_CREATE_DATABASE","database_info":{"namespace_name": "%s","quota": 1048576, "database":"%s"}}' % (ns, db)
	res, errMsg = self.post("MetaService/meta_manager", data)
	try:
	    jsres = json.loads(res)
	    return jsres['errcode'] == 'SUCCESS'
	except Exception, e:
	    return False

    def createTable(self, ns, db, tableInfo):
	data = '{"op_type":"OP_CREATE_TABLE","table_info":{"namespace_name": "%s","resource_tag": "%s", "database":"%s", "table_name":"%s", "fields":%s, "indexs":%s}}' % (ns, tableInfo['resource_tag'], db, tableInfo['table_name'], json.dumps(tableInfo['fields']), json.dumps(tableInfo['indexs']))
	res, errMsg = self.post("MetaService/meta_manager", data)
	try:
	    jsres = json.loads(res)
	    return jsres['errcode'] == 'SUCCESS'
	except Exception, e:
	    print str(e)
	    return False

    def getUserPrivileges(self):
        data = '{"op_type":"QUERY_USERPRIVILEG"}'
        res, errMsg = self.post("/MetaService/query",data)
        try:
            jsres = json.loads(res)
            if 'user_privilege' not in jsres:
                return None
            return jsres['user_privilege']
        except Exception,e:
            return None
            

    def post(self,uri,data, region_id = 0):
        res = None
        tryTimes = 3
        errorMsg = ''
        while tryTimes:
            tryTimes -= 1
            try:
                url = 'http://%s/%s' % (self.getLeader(region_id), uri)
                req = urllib2.Request(url, data)
                response = urllib2.urlopen(req, timeout = 2)
                res = response.read()
            except Exception,e:
                time.sleep(1)
                continue
            break
        if res == None:
            return res, errorMsg
        return res,''


if __name__ == '__main__':
    meta = MetaClient('10.100.217.148:9010,10.100.217.149:8010,10.100.217.150:8010')
    print meta.getLeader()
