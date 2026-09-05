"""rrweb 服务配置。"""

DATABASE_URL = "mysql+pymysql://root:99ad602410035dd4@192.168.10.230:3306/rrweb"

# 主站 token 校验：GET /api/up/auth/verify/
AUTH_VERIFY_URL = "https://y.test.yaocai.co/api/up/auth/verify/"
AUTH_VERIFY_TIMEOUT = 5
# 同一 token 校验成功结果缓存秒数；0 表示不缓存（8 小时）
AUTH_VERIFY_CACHE_TTL = 8 * 60 * 60
