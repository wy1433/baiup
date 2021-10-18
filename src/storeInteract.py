#!/usr/bin/python
#-*- coding:utf8 -*-
import time
import urllib
import sys
import urllib2
import traceback
import json

class StoreInteract():
    def __init__(self, host, port):
        self.host = host
        self.port = int(port)


 

    def getRegionList(self):
        res = None
        uri = 'StoreService/query_region'
        data = '{}'
        res = self.post(uri, data)
        if res == None:
            return None
        try:
            if 'region_leaders' not in res:
                return []
            return res['region_leaders']
        except Exception,e:
            print traceback.format_exc()
            return None

    def getRegionInfo(self, regionid):
        res = None
        uri = 'StoreService/query_region'
        data = '{"region_ids":[%d]}' % regionid
        res = self.post(uri, data)
        if res == None:
            return None
        try:
            for reg in res['regions']:
                if reg['region_id'] == regionid:
                    return reg
            return None
        except Exception,e:
            print traceback.format_exc()
            return None

    def quitLeader(self, regionid):
        return self.transferLeader(regionid, '0.0.0.0:0')

    def transferLeader(self, regionid, newleader):
        res = None
        uri = 'StoreService/region_raft_control'
        data = '{"op_type" : "TransLeader","region_id" : %d,"new_leader" : "%s"}' % (regionid, newleader)
        res = self.post(uri, data)
        if res == None:
            return None
        try:
            return res['errcode'] == 'SUCCESS'
        except Exception,e:
            print traceback.format_exc()
            return False
        

    def getIllegalRegion(self):
	res = None
	uri = 'StoreService/query_illegal_region'
	data = '{}'
        res = self.post(uri, data)
        if res == None:
            return None
        try:
            if 'region_leaders' not in res:
                return []
            return res['region_leaders']
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
                url = 'http://%s:%d/%s' % (self.host, self.port, uri)
                req = urllib2.Request(url, data)
                response = urllib2.urlopen(req)
                res = response.read()
                res = json.loads(res)
            except Exception,e:
                time.sleep(1)
                continue
            break
        if res == None:
            print traceback.format_exc()
            return res
        return res



if __name__ == '__main__':
    store = StoreInteract(sys.argv[1],8110)
    exit(0)
    print store.getRegionList()
    print store.getRegionInfo(4596)
    print store.quitLeader(4596)
    print store.getRegionInfo(4596)
    time.sleep(0.1)
    print store.getRegionInfo(4596)
