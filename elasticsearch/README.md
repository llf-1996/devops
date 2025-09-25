# 快速开始

## 准备基础配置文件
```bash
mkdir -p runtime/es/plugins
mkdir -p runtime/es/data
mkdir -p runtime/es/config
# docker pull elasticsearch:8.12.2
docker pull docker.cnb.cool/jinriyaojia_huigu/yaocai/devops/elasticsearch:8.12.2
docker run --rm -v ./runtime/es/config:/temp-config docker.cnb.cool/jinriyaojia_huigu/yaocai/devops/elasticsearch:8.12.2 cp -r /usr/share/elasticsearch/config/. /temp-config/
```

## 启动
```bash
docker compose up -d
```

## 首次启动初始化配置

### 安装插件
> 安装IK中文分词插件、拼音分词插件

```bash
PS D:\workspace\devops\elasticsearch> docker compose exec elasticsearch bash
elasticsearch@4c43c9776808:~$ ./bin/elasticsearch-plugin install https://get.infini.cloud/elasticsearch/analysis-ik/8.12.2
-> Installing https://get.infini.cloud/elasticsearch/analysis-ik/8.12.2
-> Downloading https://get.infini.cloud/elasticsearch/analysis-ik/8.12.2
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@     WARNING: plugin requires additional permissions     @
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
* java.net.SocketPermission * connect,resolve
See https://docs.oracle.com/javase/8/docs/technotes/guides/security/permissions.html
for descriptions of what these permissions allow and the associated risks.

Continue with installation? [y/N]y
-> Installed analysis-ik
-> Please restart Elasticsearch to activate any plugins installed
elasticsearch@4c43c9776808:~$
elasticsearch@4c43c9776808:~$ ./bin/elasticsearch-plugin install https://get.infini.cloud/elasticsearch/analysis-pinyin/8.12.2
-> Installing https://get.infini.cloud/elasticsearch/analysis-pinyin/8.12.2
-> Downloading https://get.infini.cloud/elasticsearch/analysis-pinyin/8.12.2
-> Installed analysis-pinyin
-> Please restart Elasticsearch to activate any plugins installed
elasticsearch@4c43c9776808:~$ exit
exit
PS D:\workspace\devops\elasticsearch>
```

### 1.1创建kibana需要的es账号
> 创建docker-compose.yml中kibana指定的账户，并账户授权

```bash
PS D:\workspace\devops\elasticsearch> docker compose exec elasticsearch bash
elasticsearch@945b86b869a5:~$ elasticsearch-users useradd elastic-kibana -p 123456 -r kibana_system
WARNING: Owner of file [/usr/share/elasticsearch/config/users] used to be [root], but now is [elasticsearch]
WARNING: Owner of file [/usr/share/elasticsearch/config/users_roles] used to be [root], but now is [elasticsearch]
elasticsearch@945b86b869a5:~$ exit
exit
PS D:\workspace\devops\elasticsearch>
```

### 1.2创建 Kibana 服务账户令牌
> 创建docker-compose.yml中kibana指定的账户

```bash
PS D:\workspace\devops\elasticsearch> docker compose exec -it elasticsearch elasticsearch-service-tokens create elastic/kibana kibana-token
SERVICE_TOKEN elastic/kibana/kibana-token = AAEAAWVsYXN0aWMva2liYW5hL2tpYmFuYS10b2tlbjpWckFhYWl4U1EyNmNRMGR4OGtXYmVR
PS D:\workspace\devops\elasticsearch>
```


> 参考文档：https://www.cnblogs.com/allay/p/18153544
