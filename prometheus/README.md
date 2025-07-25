# Prometheus Docker 部署项目

## 项目简介
本项目通过 Docker Compose 快速部署 Prometheus 服务，支持版本控制（Git）管理配置文件目录（仅跟踪目录，忽略内容）。

## 目录结构
```
prometheus/
├── docker-compose.yaml # Docker 服务配置（Prometheus 镜像及容器参数）
└── README.md           # 项目说明文档（当前文件）
```

## 安装与运行
### 前置条件
- 已安装 Docker 和 Docker Compose（建议 Docker Engine ≥ 20.10，Docker Compose ≥ 1.29）
- 已配置 Docker 国内镜像加速（可选，提升拉取速度）

### 步骤
1. 创建数据目录（Windows PowerShell）：
```bash
# 创建卷挂载目录（Linux/WSL）
mkdir -p /data/prometheus
mkdir -p /data/prometheus/config
mkdir -p /data/prometheus/data
chmod 777 -R /data/prometheus
```
2. 克隆/下载本项目到本地：
```bash
git clone git@e.coding.net:huigu8/yaocai/devops.git
cd devops/prometheus/
```
3. 启动服务：
```bash
docker-compose up -d
```
4. 访问 Prometheus 控制台：
   - 地址：`http://<你的主机IP>:11090`（默认端口 9090）

## 配置说明
- 配置文件目录：`/data/prometheus/config`（需包含prometheus.yml等配置文件）
- 数据存储目录：`/data/prometheus/data`

## 配置文件准备

Prometheus 启动前，**必须确保主机 `/data/prometheus/config` 目录下存在 `prometheus.yml` 配置文件**，否则容器会启动失败。

### 示例创建方法（Linux/WSL）：
```bash
mkdir -p /data/prometheus/config
vim /data/prometheus/config/prometheus.yml
```

### 最简单的 prometheus.yml 示例内容：
```yaml
global:
  scrape_interval: 60s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
  - job_name: 'node'
    static_configs:
      - targets: ['node-exporter:9100']
```

保存后，重启 Prometheus 容器：
```bash
docker-compose restart
```

## 注意事项
  - 生产环境建议根据实际需求重新创建数据目录并挂载数据卷，避免容器删除后数据丢失
