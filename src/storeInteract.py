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

    def getRaftInfo(self, regionid):
        res = None
        uri = 'raft_stat/region_%d' % regionid
        data = ''
        res = self.get(uri)
        return res

    def getRaftList(self):
        res = None
        uri = 'raft_stat'
        data = ''
        res = self.get(uri)
	if res == None:
	    return None
        reslist = res.split('\n\n')
        return reslist

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

    def removeRegion(self, regionID):
        uri = 'StoreService/remove_region'
        data = '{"region_id":%d, "force": true}' % regionID
        res = self.post(uri, data)
        if res == None:
            return False
        try:
            return res['errcode'] == 'SUCCESS'
        except Exception, e:
            return False

    def removePeer(self, regionID, peer):
        
        pass

    def setPeers(self, regionID, oldpeers, newpeers):
        uri = 'StoreService/region_raft_control'
        data = {'op_type':'SetPeer', 'region_id':regionID,'old_peers':oldpeers,'new_peers':newpeers}
        data = json.dumps(data,ensure_ascii=False)
        res = self.post(uri, data)
        if res == None:
            return False
        try:
            if res['errcode'] != 'SUCCESS':
               print res
            return res['errcode'] == 'SUCCESS'
        except Exception, e:
            return False

    def forceSetPeers(self, regionID, oldpeers, newpeers):
        uri = 'StoreService/region_raft_control'
        data = {'op_type':'SetPeer','force':True, 'region_id':regionID,'old_peers':oldpeers,'new_peers':newpeers}
        data = json.dumps(data,ensure_ascii=False)
        res = self.post(uri, data)
        if res == None:
            return False
        try:
            if res['errcode'] != 'SUCCESS':
               print res
            return res['errcode'] == 'SUCCESS'
        except Exception, e:
            return False


    def post(self,uri,data):
        res = None
        tryTimes = 1
        errorMsg = ''
        while tryTimes:
            tryTimes -= 1
            try:
                url = 'http://%s:%d/%s' % (self.host, self.port, uri)
                req = urllib2.Request(url, data)
                response = urllib2.urlopen(req, timeout = 1)
                res = response.read()
                res = json.loads(res)
            except Exception,e:
                continue
            break
        if res == None:
            return res
        return res

    def get(self, uri):
        tryTimes = 1
        while tryTimes:
            tryTimes -= 1
            try:
                headers = {'User-Agent':'curl/7.29.0'}
                url = 'http://%s:%d/%s' % (self.host, self.port, uri)
                req = urllib2.Request(url, headers = headers, data = '{}')
                response = urllib2.urlopen(req, timeout = 1)
                res = response.read()
                res = res.replace('\r\n','\n').strip()
                return res
            except Exception,e:
                continue
            break
        return None



if __name__ == '__main__':
    store = StoreInteract(sys.argv[1],8110)
    exit(0)
    print store.getRegionList()
    print store.getRegionInfo(4596)
    print store.quitLeader(4596)
    print store.getRegionInfo(4596)
    time.sleep(0.1)
    print store.getRegionInfo(4596)
