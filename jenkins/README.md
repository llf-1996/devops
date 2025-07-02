# Jenkins Docker 部署项目

## 项目简介
本项目通过 Docker Compose 快速部署 Jenkins 服务，支持版本控制（Git）管理 Jenkins 主目录结构（仅跟踪目录，忽略内容）。

## 目录结构
```
jenkins/
├── .gitignore       # Git 忽略规则（原用于管理 jenkins_home 目录，现目录已删除）
├── docker-compose.yaml # Docker 服务配置（Jenkins 镜像及容器参数）
└── README.md        # 项目说明文档（当前文件）
```

## 安装与运行
### 前置条件
- 已安装 Docker 和 Docker Compose（建议 Docker Engine ≥ 20.10，Docker Compose ≥ 1.29）
- 已配置 Docker 国内镜像加速（可选，提升拉取速度）

### 步骤
1. 创建数据目录（Windows PowerShell）：
```bash
# 创建卷挂载目录（Linux/WSL）
sudo mkdir -p /data/jenkins/jenkins_home
sudo chmod 777 /data/jenkins/jenkins_home


```
2. 克隆/下载本项目到本地：
```bash
git clone git@e.coding.net:huigu8/yaocai/devops.git
cd devops/jenkins/
```
3. 启动服务：
```bash
docker-compose up -d
```
4. 访问 Jenkins 控制台：
   - 地址：`http://<你的主机IP>:10080`（默认端口 8080）
   - 初始管理员密码：通过 `docker logs jenkins` 查看容器日志获取

## 配置说明
### .gitignore 规则
- `!.gitignore`：保留当前 `.gitignore` 文件（避免被自身规则忽略）

## 注意事项
  - 生产环境建议根据实际需求重新创建 `jenkins_home` 目录并挂载数据卷，避免容器删除后数据丢失
