#安装baiup 
bash install.sh





#一、部署


命令：

baiup deploy clustername version deploy.yaml



deploy.yaml文件格式如下：



global:
  version: v1.0.0.1
 
 
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
  cpu_cores: 8-15   # 规定： store0使用8-15, store1使用16-23，  storex使用  [(x+1) * 8 - (x+2) * 8)


#二、查看状态
baiup display clustername  

baiup display clustername 1.1.1.2:8110

baiup display clustername db

baiup display clustername resource_tag=tag1





#三、缩容
baiup scale-in clustername 1.1.1.1:8112



#四、扩容
baiup scale-out clustername scale-out.yaml

scale-out.yaml文件格式如下， 基本同deploy.yaml



store:
- host: 1.1.1.1
  port: 8117
  path: store7
  config:
    xx: xx


#五、升级
baiup upgrade clustername version

单节点升级为：

baiup upgrade clustername version ip:port



按照组件升级

baiup upgrade clustername version  db|meta|store



按照resource_tag升级

baiup upgrade clustername version resource_tag=tag1



#六、修改配置
baiup edit-config clustername

命令会打开编辑配置文件， 修改后保存。



#七、启动停止
根据实例

baiup start clustername ip:port

baiup stop clustername ip:port

根据类型

baiup start clustername db|meta|store 

baiup stop clustername db|meta|store 

整个集群

baiup start clustername

baiup stop clustername

按照resource_tag

baiup start cluster resource_tag=tag1

baiup stop cluster resource_tag=tag2



#八、添加维护集群
87.107目前没有维护所有集群，

有szmain  hotel  huidu  honghu

使用如下命令添加集群



baiup init clustername init.yaml



init.yaml文件如下：

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
 
store:
- host: 1.1.1.1
  port: 3333
  path: store

- host: 1.1.1.2
  port: 3333
  path: store
 



#九、查看现有集群
baiup cluster



#十、region相关命令

查询所有region：  baiup region clustername      :   可接store_id 或resource_tag=tagx
查询某个region信息： baiup region clustername info region_id
查询非法region: baiup region clustername illegal
删除非法region: baiup region clustername remove-illegal
查询没有leader的region: baiup region clustername noleader   后面可接store_id或resource_tag=tagx
统计各个instance的region梳理: baiup region clustername count
查询store和meta中leader不同的region: baiup region clustername diff
查询某个store某个region的raft信息： baiup region clustername raftinfo store_id region_id
查询某个store所有的raft信息： baiup region clustername raftlist store_id
添加peer: baiup region clustername add-peer region_id  add_peer_id
删除peer: baiup region clustername remove-peer region_d remove_peer_id
查询处于applying状态的region个数：baiup region clustername applying    后面可接store_id 或resource_tag=tagx
查询region的peercount：
查询所有region的peer数：baiup region clustername peer-count
查询某个store所有region的peer数：baiup region clustername peer-count store_id
查询peer数等于x的region数： baiup region clustername peer-count=3   后面可接store_id或resource_tag=tagx




#十一、meta相关命令


关闭负载均衡： baiup meta clustername close-balance
打开负载均衡： baiup meta clustername open-balance
查询逻辑机房： baiup meta clustername logical
查询物理机房： baiup meta clustername physical
查询store信息：baiup meta clustername instance    后面可接store_id或resource_tag=tagx
查询meta的leader：baiup meta clustername get-leader
迁移meta的leader：baiup meta clustername transfer-leader ip:port  (从此节点将leader迁走,若此节点无leader，不进行任何操作)


#十二、连接数据库
       baiup connect clustername dbname 

       baiup connect clustername dbname  dbnode


