# rrweb 后端服务

## 1. 环境准备
- Python 3.11+
- MySQL 外部数据库

## 2. 安装依赖（推荐使用阿里云源加速）
```bash
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
```

## 3. 配置

编辑 [`config.py`](config.py)（数据库连接、主站 token 校验地址等）。

## 4. 数据库迁移

表结构：`rrweb_sessions`（会话）+ `rrweb_event_details`（事件分片）。无旧数据回填，DDL 以仓库内 Alembic revision 为准。

### 开发本地（改模型后）
在 `devops/rrweb` 目录：
```bash
alembic revision --autogenerate -m "描述信息"
# 人工确认 versions 脚本后
alembic upgrade head
```
将生成的 `alembic/versions/*.py` **随代码提交仓库**。不要在部署机上临时 `revision`。

### 测试 / 生产
拉代码后执行：
```bash
alembic upgrade head
```
容器启动命令已包含 `alembic upgrade head`（见 Dockerfile），重建并重启容器即自动升到 head：
```bash
docker compose up -d --build
```

## 5. 启动服务
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 6. 访问接口文档
浏览器访问：http://localhost:8000/docs

## 7. 接口说明（摘要）

| 接口 | 说明 |
|------|------|
| `POST /events` | upsert 会话 + 插入分片；body 需 `request_id`、`record_type`、`events`，无需 `request_at` |
| `GET /events` | 会话列表，按 `updated_at` 降序 |
| `GET /events/detail` | 分片列表，按 `id` 升序（前端串行上报保证顺序） |

# 容器启动
```bash
# 首次启动
docker compose up -d
# 后续更新启动
docker compose restart
```
