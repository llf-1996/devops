# Grafana Docker 部署项目

## 项目简介
本项目通过 Docker Compose 快速部署 Grafana 服务，支持版本控制（Git）管理配置文件目录（仅跟踪目录，忽略内容）。

## 目录结构
```
grafana/
├── docker-compose.yaml # Docker 服务配置（Grafana 镜像及容器参数）
└── README.md           # 项目说明文档（当前文件）
```

## 安装与运行
### 前置条件
- 已安装 Docker 和 Docker Compose（建议 Docker Engine ≥ 20.10，Docker Compose ≥ 1.29）
- 已配置 Docker 国内镜像加速（可选，提升拉取速度）

### 步骤
1. 创建数据目录（Linux/WSL）：
```bash
mkdir -p /data/grafana/data
mkdir -p /data/grafana/provisioning
chmod 777 -R /data/grafana
```
2. 克隆/下载本项目到本地：
```bash
git clone git@e.coding.net:huigu8/yaocai/devops.git
cd devops/grafana/
```
3. 启动服务：
```bash
docker-compose up -d
```
4. 访问 Grafana 控制台：
   - 地址：`http://<你的主机IP>:11095`（默认端口 3000）
   - 默认管理员账号：admin
   - 默认管理员密码：admin（可在 docker-compose.yaml 中修改）

## 配置说明
- 数据存储目录：`/data/grafana/data`（持久化所有仪表盘、用户等数据）
- 配置目录：`/data/grafana/provisioning`（可选，自动化仪表盘、数据源等配置）

## 注意事项
  - 生产环境建议根据实际需求重新创建数据目录并挂载数据卷，避免容器删除后数据丢失 