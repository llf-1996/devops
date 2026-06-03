# Sentry 私有化部署 [![Build Status][build-status-image]][build-status-url]

基于 [Docker](https://www.docker.com/) 运行自托管 [Sentry](https://sentry.io/) 的官方引导项目。

## 环境要求

 * Docker 17.05.0+
 * Compose 1.17.0+

## 最低硬件要求

 * 至少需要 3GB 内存

## 安装

使用默认配置快速开始，只需克隆仓库并在本地目录运行 `./install.sh` 即可。

如果你需要根据自身环境调整配置（例如添加 GitHub 凭据），可能需要修改项目中的 `docker-compose.yml` 文件。如需修改，请在运行安装脚本之前完成。

推荐的配置自定义方式按优先级依次为：

 * `config.yml`
 * `sentry.conf.py`
 * `.env.example` — 环境变量模板文件（安装时会被复制为 `.env`）
 * `.env` 环境变量文件

如有任何问题或疑问，欢迎访问我们的 [社区论坛](https://forum.sentry.io/c/on-premise)！

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
