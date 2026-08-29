"""rrweb 服务配置。"""

DATABASE_URL = "mysql+pymysql://root:99ad602410035dd4@192.168.10.230:3306/rrweb"

# 主站 token 校验：GET /api/v1/auth/verify/
AUTH_VERIFY_URL = "https://y.yaocai.co/api/v1/auth/verify/"
AUTH_VERIFY_TIMEOUT = 5
