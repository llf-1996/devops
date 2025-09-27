# 快速开始

## 准备基础配置文件
```bash
mkdir -p runtime/es/plugins && mkdir -p runtime/es/data && mkdir -p runtime/es/config && mkdir -p runtime/es/logs
# 修改文件权限，解决配置文件复制和IK中文分词插件安装权限问题
chown -R 1000:1000 runtime
docker run --rm -v ./runtime/es/config:/temp-config docker.cnb.cool/jinriyaojia_huigu/yaocai/devops/elasticsearch:8.12.2 cp -r /usr/share/elasticsearch/config/. /temp-config/
# 创建同义词文件
mkdir -p runtime/es/config/certs && touch runtime/es/config/certs/synonym.txt
```

## 启动
```bash
# 设置环境变量，修改.env文件中的变量
cp .env.example .env
cat .env
docker compose up -d
```

## 首次启动初始化配置

### 安装插件
> 安装IK中文分词插件、拼音分词插件

```bash
[root@yaocai-local-dev elasticsearch]# docker compose exec elasticsearch bash
elasticsearch@33d5877b32ba:~$ ./bin/elasticsearch-plugin install https://get.infini.cloud/elasticsearch/analysis-ik/8.12.2
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
elasticsearch@33d5877b32ba:~$ 
elasticsearch@33d5877b32ba:~$ 
elasticsearch@33d5877b32ba:~$ ./bin/elasticsearch-plugin install https://get.infini.cloud/elasticsearch/analysis-pinyin/8.12.2
-> Installing https://get.infini.cloud/elasticsearch/analysis-pinyin/8.12.2
-> Downloading https://get.infini.cloud/elasticsearch/analysis-pinyin/8.12.2
-> Installed analysis-pinyin
-> Please restart Elasticsearch to activate any plugins installed
elasticsearch@33d5877b32ba:~$ exit
exit
[root@yaocai-local-dev elasticsearch]# 
```
###  配置Kibana 连接 Elasticsearch 的身份验证凭据
#### 1.1创建kibana需要的es账号
> 设置docker-compose中指的es内置账号（kibana_system）用于kibana访问es
> 密码：CfHhxf8fzv，修改密码需同步修改docker-compose.yml中kibana指定的账号密码

```bash
[root@VM-4-10-centos elasticsearch]# docker compose exec elasticsearch bash
elasticsearch@0a5d8d64466e:~$ elasticsearch-reset-password -i -u kibana_system
This tool will reset the password of the [kibana_system] user.
You will be prompted to enter the password.
Please confirm that you would like to continue [y/N]y


Enter password for [kibana_system]: 
Re-enter password for [kibana_system]: 
Password for the [kibana_system] user successfully reset.
elasticsearch@0a5d8d64466e:~$ 
```

> 创建账号示例
```bash
[root@yaocai-local-dev elasticsearch]# docker compose exec elasticsearch bash
elasticsearch@33d5877b32ba:~$ 
elasticsearch@33d5877b32ba:~$ elasticsearch-users useradd elastic-test -p 123456 -r kibana_system
WARNING: Group of file [/usr/share/elasticsearch/config/users] used to be [root], but now is [elasticsearch]
WARNING: Group of file [/usr/share/elasticsearch/config/users_roles] used to be [root], but now is [elasticsearch]
elasticsearch@33d5877b32ba:~$ exit
exit
[root@yaocai-local-dev elasticsearch]#
```

#### 1.2创建 Kibana 服务账户令牌
> 创建docker-compose.yml中kibana指定的账户

```bash
PS D:\workspace\devops\elasticsearch> docker compose exec -it elasticsearch elasticsearch-service-tokens create elastic/kibana kibana-token
SERVICE_TOKEN elastic/kibana/kibana-token = AAEAAWVsYXN0aWMva2liYW5hL2tpYmFuYS10b2tlbjpWckFhYWl4U1EyNmNRMGR4OGtXYmVR
PS D:\workspace\devops\elasticsearch>
```

### 配置完成后重启es
```bash
docker compost researt elasticsearch
```

## 访问服务
### ES
```bash
http://127.0.0.1:19200
```

### kibana
```bash
http://127.0.0.1:5601
```


# 操作示例
## kibana创建索引
```bash
# 为所有 .kibana*索引（如 .kibana, .kibana_1等）统一应用配置，解决磁盘空间问题：通过减少分片和副本数量（1主分片+0副本），显著降低存储开销
PUT _index_template/.kibana
{
  "index_patterns": [".kibana*"],
  "template": {
    "settings": {
      "number_of_shards": 1,
      "number_of_replicas": 0,
      "auto_expand_replicas": false
    }
  },
  "priority": 1
}


# 新建索引
PUT /yaocai_drug
{
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0,
        "analysis": {
            "filter": {  
              "synonym_filter": {  
                "type": "synonym",
                "synonyms_path": "certs/synonym.txt"  
              }
            }, 
            "analyzer": {
                "pinyin_analyzer": {
                    "tokenizer": "my_pinyin"
                },
                "synonym_analyzer": {  
                  "tokenizer": "standard",  
                  "filter": ["lowercase", "synonym_filter"]  
                }
            },
            "tokenizer": {
                "my_pinyin": {
                    "type": "pinyin",
                    "keep_first_letter": false,
                    "keep_separate_first_letter": true,
                    "keep_full_pinyin": true,
                    "keep_original": false,
                    "keep_none_chinese_together": true,
                    "limit_first_letter_length": 16,
                    "lowercase": true,
                    "remove_duplicated_term": true
                }
            }
        }
    },
    "mappings": {
        "properties": {
            "update_time": {
                "type": "date",
                "format": "strict_date_optional_time||epoch_millis",
                "store": true
            },
            "is_delete": {
                "type": "boolean",
                "store": true
            },
            "name": {
                "type": "text",
                "fields": {
                    "keyword": {
                        "type": "keyword",
                        "ignore_above": 256
                    },
                    "pinyin": {
                        "type": "text",
                        "store": false,
                        "term_vector": "with_offsets",
                        "analyzer": "pinyin_analyzer"
                    }
                }
            },
            "trade_name": {
                "type": "text",
                "fields": {
                    "keyword": {
                        "type": "keyword",
                        "ignore_above": 256
                    },
                    "pinyin": {
                        "type": "text",
                        "store": false,
                        "term_vector": "with_offsets",
                        "analyzer": "pinyin_analyzer"
                    }
                }
            },
            "alias_name": {
                "type": "text",
                "fields": {
                    "keyword": {
                        "type": "keyword",
                        "ignore_above": 256
                    },
                    "pinyin": {
                        "type": "text",
                        "store": false,
                        "term_vector": "with_offsets",
                        "analyzer": "pinyin_analyzer"
                    }
                }
            },
            "specification": {
                "type": "text",
                "fields": {
                    "keyword": {
                        "type": "keyword",
                        "ignore_above": 256
                    },
                    "pinyin": {
                        "type": "text",
                        "store": false,
                        "term_vector": "with_offsets",
                        "analyzer": "pinyin_analyzer"
                    }
                }
            },
            "specification2": {
                "type": "text",
                "analyzer": "synonym_analyzer"
            },
            "price": {
                "type": "float",
                "store": true
            },
            "factory": {
                "type": "text",
                "fields": {
                    "keyword": {
                        "type": "keyword",
                        "ignore_above": 256
                    },
                    "pinyin": {
                        "type": "text",
                        "store": false,
                        "term_vector": "with_offsets",
                        "analyzer": "pinyin_analyzer"
                    }
                }
            },
            "barcode": {
                "type": "keyword",
                "store": true
            },
            "classify_id": {
                "type": "keyword",
                "store": true
            },
            "status": {
                "type": "integer",
                "store": true
            },
            "is_otc": {
                "type": "boolean",
                "store": true
            },
            "in_medical_insurance": {
                "type": "boolean",
                "store": true
            },
            "medical_insurance_code": {
                "type": "keyword",
                "store": true
            },
            "brand": {
                "type": "text",
                "fields": {
                    "keyword": {
                        "type": "keyword",
                        "ignore_above": 256
                    }
                }
            },
            "unit": {
                "type": "keyword",
                "store": true
            },
            "approval": {
                "type": "text",
                "fields": {
                    "keyword": {
                        "type": "keyword",
                        "ignore_above": 256
                    }
                }
            },
            "business_type_text": {
                "type": "keyword",
                "store": true
            },
            "images": {
                "type": "keyword",
                "store": true
            },
            "upc": {
                "type": "keyword",
                "store": true
            }
        }
    }
}


# 删除索引
DELETE /yaocai_drug


# 查询文档总数
GET /yaocai_drug/_count


# 查询示例
GET /yaocai_drug/_search
{  
  "query": {  
    "bool": {  
      "should": [  
        {  
          "match_phrase": {  
            "name": {  
              "query": "感冒颗粒",  
              "boost": 10,
              "slop": 15   
            }  
          }  
        },  
        {
          "match_phrase": {  
            "factory": {  
              "query": "感冒颗粒",  
              "boost": 1,
              "slop": 15   
            }  
          }  
        },
        {  
          "match_phrase": {  
            "factory.pinyin": {  
              "query": "感冒颗粒",  
              "boost": 1,
              "slop": 15   
            }  
          }  
        },
        {  
          "match_phrase": {  
            "name.pinyin": {  
              "query": "感冒颗粒",  
              "boost": 1,
              "slop": 15   
            }  
          }  
        },
        {  
          "match_phrase": {  
            "brand": {  
              "query": "感冒颗粒",  
              "boost": 1,
              "slop": 15   
            }  
          }  
        }
      ],  
      "minimum_should_match": 1 
    }  
  },
  "aggs": {  
    "group_by_name_keyword": {  
      "terms": {  
        "field": "name.keyword",  
        "size": 100 
      }  
    },
    "group_by_factory_keyword": {  
      "terms": {  
        "field": "factory.keyword",  
        "size": 100  
      }  
    },
    "group_by_specification_keyword": {  
      "terms": {  
        "field": "specification.keyword",  
        "size": 100
      }  
    }
  }
}
```


## 数据同步（logstash）
> 参考

### 全量
```bash
/usr/share/logstash/bin/logstash -f all_yaocai_drug.conf
```

```config
# all_yaocai_drug.conf
# pipeline.ecs_compatibility: disabled
input {
  # 全量同步
  jdbc {
    jdbc_connection_string => "jdbc:postgresql://192.168.10.230:5432/yaocai_dev2"
    jdbc_user => "yaocai_dev"
    jdbc_password => "hEFWbfsEkzEEMcj6"
    jdbc_driver_library => "/root/logstash/postgresql-42.7.3.jar"
    jdbc_driver_class => "org.postgresql.Driver"  
    jdbc_page_size => 1000
    jdbc_fetch_size => 1000

    statement => "SELECT id,update_time,is_delete,name,specification,price,factory,classify_id,barcode,status,is_otc,in_medical_insurance,medical_insurance_code,brand,unit,approval,business_type_text,images,upc,trade_name,alias_name FROM yaocai_drug where is_delete = false order by id asc;"

    # 重复执行的周期，每分钟执行1次
    #schedule => "* * * * *"
    
    # 是否将字段名小写化
    #lowercase_column_names => false
      
    # 增量同步的参数
    #use_column_value => true
    #tracking_column => "id"
    #record_last_run => true
    #last_run_metadata_path => "/root/logstash/your_last_run_metadata_file"

    # 启用调试日志
    #jdbc_validate_connection => true
    #jdbc_pagination_enabled => false
  }
}

# 规格添加一个新的格式，数字与英文分隔
filter {
  if [specification] {
    ruby {
      code => "
        spec = event.get('specification')
        # 使用正则表达式将所有的数字和字母之间插入空格
        spec_modified = spec.gsub(/(\d+(\.\d+)?)([a-zA-Z*]+)/, '\\1 \\3')
        
        event.set('specification2', spec_modified)
      "
    }
  }
}

output {
  elasticsearch {
    hosts => ["http://127.0.0.1:19200"]
    index => "yaocai_drug"

    document_id => "%{id}"
    
    manage_template => false

    user => "elastic"
    password => "dAUl36wBVN"
  }

  # 可以添加stdout输出用于调试
  #stdout { codec => rubydebug }
}
```

### 增量
```config
# pipeline.ecs_compatibility: disabled
input {
  # 增量同步
  jdbc {  
    jdbc_connection_string => "jdbc:postgresql://192.168.10.230:5432/yaocai_dev2"   
    jdbc_user => "yaocai_dev"  
    jdbc_password => "hEFWbfsEkzEEMcj6"  
    jdbc_driver_library => "/root/logstash/postgresql-42.7.3.jar"  
    jdbc_driver_class => "org.postgresql.Driver"
    jdbc_page_size => 1000
    jdbc_fetch_size => 1000

    statement => "SELECT id,update_time,is_delete,name,specification,price,factory,classify_id,barcode,status,is_otc,in_medical_insurance,medical_insurance_code,brand,unit,approval,business_type_text,images,upc,trade_name,alias_name FROM yaocai_drug where update_time > :sql_last_value order by update_time asc;"

    # 重复执行的周期，每分钟执行1次
    schedule => "*/3 * * * *"  
    
    # 是否将字段名小写化
    #lowercase_column_names => false  
      
    # 增量同步的参数  
    use_column_value => true  
    tracking_column => "update_time"  
    tracking_column_type => "timestamp"
    record_last_run => true  
    last_run_metadata_path => "/root/logstash/your_last_run_metadata_file"  

    # 启用调试日志  
    #jdbc_validate_connection => true  
    #jdbc_pagination_enabled => false  
  }  
}

# 规格添加一个新的格式，数字与英文分隔
filter {  
  if [specification] {
    ruby {  
      code => "
        spec = event.get('specification')
        # 使用正则表达式将所有的数字和字母之间插入空格
        spec_modified = spec.gsub(/(\d+(\.\d+)?)([a-zA-Z*]+)/, '\\1 \\3')
        
        event.set('specification2', spec_modified)  
      "  
    }  
  }  
}

output {  
  elasticsearch {  
    hosts => ["http://127.0.0.1:19200"]  
    index => "yaocai_drug"  

    document_id => "%{id}"  
    
    manage_template => false

    user => "elastic"
    password => "dAUl36wBVN"
  }

  # 可以添加stdout输出用于调试  
  #stdout { codec => rubydebug }  
}
```





> 参考文档：https://www.cnblogs.com/allay/p/18153544
