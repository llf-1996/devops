"""rrweb 服务配置。"""

# 数据库连接串（账号@主机/库名），异步与同步驱动共用同一份来源
_DATABASE_DSN = "root:99ad602410035dd4@192.168.10.230:3306/rrweb"
# 服务运行时使用异步驱动
DATABASE_URL = f"mysql+asyncmy://{_DATABASE_DSN}"
# Alembic 迁移使用同步驱动
DATABASE_URL_SYNC = f"mysql+pymysql://{_DATABASE_DSN}"

# 主站 token 校验：GET /api/up/auth/verify/
AUTH_VERIFY_URL = "https://y.test.yaocai.co/api/up/auth/verify/"
AUTH_VERIFY_TIMEOUT = 5
# 同一 token 校验成功结果缓存秒数；0 表示不缓存（8 小时）
AUTH_VERIFY_CACHE_TTL = 8 * 60 * 60
