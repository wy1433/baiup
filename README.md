使用baiup部署baikaldb
===



一、安装baiup
===

机器准备
-------
Ansible需要安装在一台发布机上，通过建立信任关系，对多台部署机进行远程部署。

|部署组件  |	主机IP   |
|  ---     |         --- |
|baiup	   |       xx.xx.xx.153|
|Meta	   |       xx.xx.xx.99, xx.xx.xx.136, xx.xx.xx.156|
|Store	   |       xx.xx.xx.99, xx.xx.xx.136, xx.xx.xx.156|
|db	   |       xx.xx.xx.99, xx.xx.xx.136, xx.xx.xx.156|


环境准备
-------

A. 配置免密登录
参考[配置免密关系](https://github.com/baidu/BaikalDB/wiki/Ansible-for-BaikalDB#4-%E5%BB%BA%E7%AB%8B%E4%BF%A1%E4%BB%BB%E5%85%B3%E7%B3%BB)<br/>
B. 部署机器安装supervise。


安装依赖
-------
```
#中控机执行
pip install paramiko
```

安装baiup
-------
```
git clone https://github.com/baikalgroup/BaikalDB-Migrate
cd BaikalDB-Migrate
cp -r baiup ~/.baiup
echo "export PATH" >> ~/.bash_profile
echo "export PATH=~./baiup/bin:$PATH" >> ~/.bash_profile
source ~/.bash_profile
```



二、部署baikaldb
===

```
baiup deploy clustername v2.0.1 deploy.yaml
```


deploy.yaml文件格式如下：

```
global:
  version: v2.0.1
 
 
#公共配置
server_config:
  meta:
    raft_max_election_delay_ms: 200
  store:
    raft_max_election_delay_ms: 100
  db:
    default_2pc: true
 
 
meta:
- host: 1.1.1.1
  port: 8010
  path: meta
  config:
    #实例独有的配置写这里
    raft_max_election_delay_ms: 100
    ...
 
 
- host: 1.1.1.2
  port: 8010
  path: meta
 
 
db:
- host: 1.1.1.1
  port: 28282
  path: db
  config:
    default_2pc: false
 
 
 
 
store:
- host: 1.1.1.1
  port: 8110
  path: store
#  cpu_cores: 8-15   # 绑定的cpu
```


三、查看状态
===

```
#查看整个集群的状态
baiup display clustername  

#查看某个实例的状态
baiup display clustername 1.1.1.2:8110

#查看所有db(store, meta)的状态
baiup display clustername db

#查看所有resource_tag=tag1的实例的状态
baiup display clustername resource_tag=tag1
```





四、缩容
===
```
baiup scale-in clustername 1.1.1.1:8112
```


五、扩容
===
```
baiup scale-out clustername scale-out.yaml
```

scale-out.yaml文件格式如下， 基本同deploy.yaml
```
store:
- host: 1.1.1.1
  port: 8117
  path: store7
  config:
    xx: xx
```


六、升级
===
```
baiup upgrade clustername version
```
单节点升级为：
```
baiup upgrade clustername version ip:port
```

按照组件升级
```
baiup upgrade clustername version  db|meta|store
```


按照resource_tag升级
```
baiup upgrade clustername version resource_tag=tag1
```


七、修改配置
===
```
baiup edit-config clustername
```
命令会打开编辑配置文件， 修改后保存。



八、启动停止
===
根据实例
```
baiup start clustername ip:port
baiup stop clustername ip:port
```
根据类型
```
baiup start clustername db|meta|store 

baiup stop clustername db|meta|store 
```
整个集群
```
baiup start clustername

baiup stop clustername
```
按照resource_tag
```
baiup start cluster resource_tag=tag1

baiup stop cluster resource_tag=tag2
```


九、添加维护集群
===
添加现有集群到baiup
```
baiup init clustername init.yaml
```

init.yaml文件如下：同deploy.yaml
```
global:
  version: 1.1.1.1
 
 
db: #db 列表，只需要host, port, path，就行
- host: 1.1.1.1
  port: 2111
  path: db
 
 
meta: #meta列表，只需host，port， path
- host: 1.1.1.1
  port: 2222
  path: meta
 
store: #store列表，只需host, port, path
- host: 1.1.1.1
  port: 3333
  path: store

- host: 1.1.1.2
  port: 3333
  path: store
``` 



十、查看现有集群
===
```
baiup cluster
```


十一、region相关命令
===

查询所有region：  
```
baiup region clustername [store_addr|resource_tag=tagx]
```
查询某个region信息：
```
baiup region clustername info region_id
```
查询非法region: 
```
baiup region clustername illegal
```
删除非法region: 
```
baiup region clustername remove-illegal
```
查询没有leader的region: 
```
baiup region clustername noleader
```

统计各个instance的region: 
```
baiup region clustername count
```
查询store和meta中leader不同的region: 
```
baiup region clustername diff
```
查询某个store某个region的raft信息： 
```
baiup region clustername raftinfo store_id region_id
```
查询某个store所有的raft信息： 
```
baiup region clustername raftlist store_id
```
添加peer: 
```
baiup region clustername add-peer region_id  store_addr
```
删除peer: 
```
baiup region clustername remove-peer region_d store_addr
```
查询处于applying状态的region个数：
```
baiup region clustername applying [store_addr|resource_tag=tagx]
```
查询所有region的peer数：
```
baiup region clustername peer-count
```
查询某个store所有region的peer数：
```
baiup region clustername peer-count store_id
```
查询peer数等于x的region数： 
```
baiup region clustername peer-count=3 [store_addr|resource_tag=tagx]
```

十二、meta相关命令
===

关闭负载均衡： 
```
baiup meta clustername close-balance
```
打开负载均衡： 
```
baiup meta clustername open-balance
```
查询逻辑机房： 
```
baiup meta clustername logical
```
查询物理机房： 
```
baiup meta clustername physical
```
查询store信息：
```
baiup meta clustername instance [store_addr|resource_tag=tagx]
```
查询meta的leader：
```
baiup meta clustername get-leader
```
迁移meta的leader：
```
baiup meta clustername transfer-leader ip:port  #从此节点将leader迁走,若此节点无leader，不进行任何操
```


十三、连接数据库
===
连接到某个库
```
baiup connect clustername dbname 
```

使用特定DB连接到某个库
```
baiup connect clustername dbname  dbnode
```

也可以选择连接哪个库

```
baiup connect clustername
```
然后选择库名或序号
