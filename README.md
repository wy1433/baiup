# 使用baiup部署baikaldb集群

baiup是baikaldb集群运维管理工具，提供部署、启动、关闭、升级，配置、扩缩容、集群状态、集群管理、集群运维命令、数据库连接等功能。

## 第1步：软硬件环境准备

* **机器准备**
    
    baiup需要安装在一台发布机上，通过建立信任关系，对多台部署机进行远程部署。

    |部署组件  |	主机IP   |
    |  ---     |         --- |
    |baiup	   |       192.168.1.4|
    |Meta	   |       192.168.1.1, 192.168.1.2, 192.168.1.3|
    |Store	   |       192.168.1.1, 192.168.1.2, 192.168.1.3|
    |db	       |       192.168.1.1, 192.168.1.2, 192.168.1.3|


* **环境准备**

    * 配置免密登录（中控机到baikaldb集群机器）
    参考[配置免密关系](https://github.com/baidu/BaikalDB/wiki/Ansible-for-BaikalDB#4-%E5%BB%BA%E7%AB%8B%E4%BF%A1%E4%BB%BB%E5%85%B3%E7%B3%BB)<br/>
    * 在中控机安装baiup依赖： ``` pip install paramiko #中控机执行 ```
    * 在baikaldb机器安装服务守护工具：supervise


## 第2步：在中控机器上安装baiup

```
git clone https://github.com/baikalgroup/baiup
mv baiup ~/.baiup
echo "export PATH" >> ~/.bash_profile
echo "export PATH=~./baiup/bin:$PATH" >> ~/.bash_profile
source ~/.bash_profile
```

## 第3步：编写集群拓扑文件
根据集群部署拓扑，编辑baiup所需的集群初始化配置文件，YAML格式。

deploy.yaml文件实例如下：

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
    # ...
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

## 第4步：执行部署命令

```
baiup deploy clustername v2.0.1 deploy.yaml
```

## 第5步：查看baiup管理的集群列表
```
baiup cluster
```

## 第6步：查看部署的集群状态

```
#查看整个集群的状态
baiup display clustername  
# 输出如下代表集群正常启动：
192.168.1.1:8010	meta		113d	 UP !
192.168.1.2:8010	meta		112d	 UP !
192.168.1.3:8010	meta		161d	 UP !
192.168.1.1:8110	store		112d	 NORMAL !	4356
192.168.1.2:8110	store		112d	 NORMAL !	4354
192.168.1.3:8110	store		112d	 NORMAL !	4348
192.168.1.1:28282	db		    113d	 UP !
192.168.1.2:28282	db		    113d	 UP !
192.168.1.3:28282	db		    112d	 UP !

#查看某个实例的状态
baiup display clustername 1.1.1.2:8110

#查看所有db(store, meta)的状态
baiup display clustername db

#查看所有resource_tag=tag1的实例的状态
baiup display clustername resource_tag=tag1
```

# 探索更多
至此，你已经完成了使用baiup部署baikaldb集群；
后续，在日常运维中，你可能还需要使用以下更多功能，欢迎一起使用与完善：

## 启动、停止集群
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

## 缩容

```
baiup scale-in clustername 1.1.1.1:8112
```

## 扩容
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


## 升级
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

## 修改配置
```
baiup edit-config clustername
```
命令会打开编辑配置文件， 修改后保存。


## 添加维护集群
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


## region相关命令

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

## meta相关命令

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
## 连接数据库
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


