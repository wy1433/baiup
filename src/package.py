#-*- coding:utf8 -*-
from common import *
import tarfile
import os
import urllib
import urllib2
import requests

class Package():
    def __init__(self, version):
	self.version = version
	
    def is_local(self):
	repoDir = os.path.join(REPO_DIR, self.version)
	if os.path.exists(repoDir):
	    return True
	
    def download(self):
	tmpDir = os.path.join(REPO_DIR, 'tmp')
	if not os.path.exists(os.path.join(tmpDir, self.version)):
	    os.makedirs(os.path.join(tmpDir, self.version))
	#gitaddr = 'https://github.com/baidu/BaikalDB/releases/download/%s/baikal-all-%s-centos-7.tgz' % (self.version, self.version)
	gitaddr = 'http://10.100.217.153:80/package/%s.tgz' % self.version
	print gitaddr
	print "downloading package ",self.version
	localFile = os.path.join(tmpDir, self.version + '.tgz')
	if os.path.exists(localFile):
	    os.remove(localFile)
	try:
	    urllib.urlretrieve(gitaddr, localFile)
	except Exception, e:
	    print "download package %s faild!" % self.version
	    print str(e)
	    exit(0)
	print "download package %s success" % self.version

	#解压
	tmpPackageDir = os.path.join(tmpDir, self.version)
	os.removedirs(tmpPackageDir)
	os.makedirs(tmpPackageDir)
	tarobj = tarfile.open(localFile, "r:gz")
	for tarinfo in tarobj:
	    print tarinfo.name
	    tarobj.extract(tarinfo.name, tmpPackageDir)
	tarobj.close()

	repoDir = os.path.join(REPO_DIR, self.version)
	os.makedirs(repoDir)
	os.rename(tmpPackageDir, repoDir)


if __name__ == '__main__':
    pkg = Package('v2.0.1')
    pkg.download()
