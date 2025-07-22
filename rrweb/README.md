# rrweb 后端服务

## 1. 环境准备
- Python 3.11+
- MySQL 外部数据库

## 2. 安装依赖（推荐使用阿里云源加速）
```bash
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
```

## 3. 配置数据库连接
在项目根目录下新建 `.env` 文件，内容如下（请根据实际情况修改）：
```
DATABASE_URL=mysql+pymysql://用户名:密码@数据库地址:3306/数据库名
```
或直接设置环境变量：
```
export DATABASE_URL=mysql+pymysql://用户名:密码@数据库地址:3306/数据库名
```

## 4. 数据库迁移
> alembic
### 后续模型变更时迁移
```bash
alembic revision --autogenerate -m "描述信息"
alembic upgrade head
```

## 5. 启动服务
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 6. 访问接口文档
浏览器访问：http://localhost:8000/docs

# 容器启动
```bash
# 首次启动
docker compose up -d
# 后续更新启动
docker compose restart
```
