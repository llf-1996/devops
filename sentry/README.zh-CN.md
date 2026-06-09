# Sentry 私有化部署 [![Build Status][build-status-image]][build-status-url]

基于 [Docker](https://www.docker.com/) 运行自托管 [Sentry](https://sentry.io/) 的官方引导项目。

## 环境要求

 * Docker 17.05.0+
 * Compose 1.17.0+

## 最低硬件要求

官方 [onpremise 9.1.2](https://github.com/getsentry/onpremise/blob/9.1.2/README.md) 写的是：

> **You need at least 3GB RAM**

这是指 **整套 docker-compose 所有容器合计**（web + worker + postgres + redis + …），**不是** web 单容器上限。

| 版本 | 官方最低内存 | 说明 |
|------|-------------|------|
| **Sentry 9.1.2**（当前） | **3GB 整机** | 轻量架构，无 Kafka/ClickHouse |
| Sentry 21+（新版 self-hosted） | **16GB 整机** | 架构完全不同，不可类比 |

实测 dev 环境各容器常驻约：web **~2G**、worker ~130MB、其余 ~200MB，**合计 ~2.3G**，符合 9.1.2 的 3GB 量级。

因此：

- web 容器 `docker stats` 显示 **~2G / 2G（100%）** 并不等于配置错误，而是 **web 占了整机内存的大头**
- 把 web 的 `mem_limit` 调到 3G 仍显示 100%，是 **cgroup 上限变大后进程 RSS 仍接近上限**（或显示四舍五入），不代表 Sentry「需要 3G 才能跑 web」
- 建议宿主机给 Docker **至少 4～6GB**，留出 OS 和其它进程余量（官方 3GB 偏紧）

## 安装

使用默认配置快速开始，只需克隆仓库并在本地目录运行 `./install.sh` 即可。

如果你需要根据自身环境调整配置（例如添加 GitHub 凭据），可能需要修改项目中的 `docker-compose.yml` 文件。如需修改，请在运行安装脚本之前完成。

推荐的配置自定义方式按优先级依次为：

 * `config.yml`
 * `sentry.conf.py`
 * `.env.example` — 环境变量模板文件（安装时会被复制为 `.env`）
 * `.env` 环境变量文件

如有任何问题或疑问，欢迎访问我们的 [社区论坛](https://forum.sentry.io/c/on-premise)！

## 启动与访问

安装完成后，启动所有服务：

```sh
docker-compose up -d
```

默认将 Web 服务映射到主机的 **11086** 端口（见 `docker-compose.yml` 中 `web` 服务的 `ports` 配置），在浏览器中访问：

| 场景 | 访问地址 |
|------|----------|
| 本机 | http://localhost:11086 |
| 远程服务器 | http://<服务器IP>:11086 |

首次登录前需创建管理员账号。若安装时未交互式创建，可执行：

```sh
docker-compose run --rm web createuser
```

按提示填写邮箱、密码等信息后即可登录 Web 界面。

> 若需通过域名访问或启用 HTTPS，请修改 `config.yml` 中的 `system.url-prefix`，并在前置代理（如 Nginx）中配置反向代理与证书。

## 内存说明

与官方 9.1.2 一致，**不设容器 `mem_limit`**，由宿主机统一管控内存。官方要求宿主机至少 **3GB RAM**（整套服务合计）。

dev 环境典型实际占用（`docker stats`）：

| 服务 | 约占用 | 说明 |
|------|--------|------|
| web | ~2G | uWSGI 1 worker + 4 threads（见 `sentry.conf.py`） |
| worker | ~130MB | Celery 并发 2 |
| 其余 | ~200MB | postgres、redis、memcached、cron、smtp |

合计约 **2.3G**，满足官方 3GB 最低要求。建议宿主机给 Docker **4～6GB**，留 OS 余量。

uWSGI 调优见 `sentry.conf.py`（`workers: 1`、`MALLOC_ARENA_MAX=2` 等）。若需显著降低 web 内存，需 **升级 Sentry 版本**。

## 目录结构

```
├── Dockerfile              # Docker 镜像构建文件
├── docker-compose.yml      # 多容器编排配置
├── .dockerignore           # Docker 构建忽略规则
├── .env.example            # 环境变量模板文件
├── config.yml              # Sentry 主配置文件
├── sentry.conf.py          # Sentry Python 配置文件
├── requirements.txt        # Python 依赖清单
├── Makefile                # 构建/推送快捷命令（build, push, all）
├── install.sh              # 一键安装脚本
├── test.sh                 # 冒烟测试脚本
├── .travis.yml             # CI 持续集成配置（Travis CI）
├── .gitignore              # Git 忽略规则
├── LICENSE                 # 许可证文件（BSL 1.1）
├── README.md               # 英文说明文档
└── README.zh-CN.md         # 中文说明文档
```

## 配置 SSL/TLS 保护 Sentry

如果你想使用 SSL/TLS 保护你的 Sentry 服务，可以使用 [HAProxy](http://www.haproxy.org/) 或 [Nginx](http://nginx.org/) 等优秀的 SSL/TLS 代理。通常你需要将此代理服务添加到 `docker-compose.yml` 文件中。

## 更新 Sentry

使用 Compose 更新 Sentry 相对简单，按以下步骤操作即可。请确保 Dockerfile 中已设置为最新版本，或直接使用本仓库的最新版本。

更新仓库或 Dockerfile 后执行以下步骤：

```sh
docker-compose build --pull   # 更新后重新构建服务，确保补丁版本为最新
docker-compose run --rm web upgrade  # 运行新的数据库迁移
docker-compose up -d           # 重新创建并启动服务
```

## 相关资源

 * [官方文档](https://docs.sentry.io/server/installation/docker/)
 * [Bug 追踪](https://github.com/getsentry/onpremise/issues)
 * [社区论坛](https://forum.sentry.io/c/on-premise)
 * [IRC](irc://chat.freenode.net/sentry) (chat.freenode.net, #sentry)


[build-status-image]: https://api.travis-ci.com/getsentry/onpremise.svg?branch=master
[build-status-url]: https://travis-ci.com/getsentry/onpremise
