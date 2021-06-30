## baiup

### 部署集群

编写yaml文件，如storage/config/deploy.yaml

```
python src/main.py deploy clusterName deploy.yaml
```

### 升级集群
升级集群可选择全升级， 升级db或store或meta， 升级某个节点

```
#升级集群, meta, store, db依次升级
python src/main.py upgrade clustername

#升级db
python src/main.py upgrade clustername db

#升级单个节点
python src/main.py upgrade clustername 172.12.22.222:28282

```

### 启动和停止
参数同上， 可对整个集群，或db/store/meta，或某个节点

```
python src/main.py start/stop clustername [db/meta/store/node]
```

### 缩容，scale-in
```
#一次只能缩容一个节点，若缩容store， 则第一次运行后，set_instance_dead, 然后使用display查看，若状态变为TOMBSTONE, 则再次运行后下线。
python src/main.py scale-in clustername 172.1.11.111:8111
```

### 扩容 scale-out
编写扩容yaml文件，如 storage/config/scale-out.yaml
```
python src/main.py scale-out clustername ./scale-out.yaml
```


### 查看状态 display

```
python src/main.py display clustername
```

### 修改集群配置 edit-config
```
###只能修改服务配置， 修改后默认推送到服务器上并重启服务。
python src/main.py edit-config clustername
```

### 更新脚本
```
#可更新restart_by_supervise.sh或stop.sh或run.sh， 可对整个集群更新，或所有db/store/meta，或某个节点
python main.py update clustername config|script|ss.sh [module|node]
```


### 初始化部署配置
线上集群现在都没有在baiup中管理，需要初始化配置，
编写yaml文件，如 storage/config/init.yaml
运行init命令
```
python src/main.py init clustername ./init.yaml
```


