#!/usr/bin/python
#-*- coding:utf8 -*-

import os
LOCAL_ROOT_DIR = os.path.join(os.environ['HOME'], ".baiup")
LOCAL_CACHE_DIR=LOCAL_ROOT_DIR + "/storage/oplist"
LOCAL_SCRIPT_DIR=LOCAL_ROOT_DIR + "/script"
REPO_DIR=LOCAL_ROOT_DIR + "/repo"
BIN_NAME_DICT={"db":"baikaldb","meta":"baikalMeta","store":"baikalStore"}
CLUSTER_DIR=LOCAL_ROOT_DIR + "/storage/clusters"
