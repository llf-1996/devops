# rrweb 后端服务

用户端前端录制并分片上报；管理端前端列表筛选与回放。

## 1. 环境准备

- Python 3.11+
- MySQL 外部数据库

服务为**全协程**实现：路由、鉴权、数据库访问均为 `async/await`。数据库走 SQLAlchemy 异步引擎 + `asyncmy`，主站鉴权走 `httpx.AsyncClient`；`pymysql` 仅供 Alembic 迁移使用。

## 2. 安装依赖（推荐使用国内 PyPI 镜像加速）

```bash
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
```

## 3. 配置

编辑 [`config.py`](config.py)（数据库连接、主站 token 校验地址 `AUTH_VERIFY_URL` 等）。

数据库连接串由同一份 `_DATABASE_DSN` 派生出两个变量，改库只需改 DSN 一处：

| 配置项 | 驱动 | 用途 |
|--------|------|------|
| `DATABASE_URL` | `mysql+asyncmy` | 服务运行时异步会话（[`app/database.py`](app/database.py)） |
| `DATABASE_URL_SYNC` | `mysql+pymysql` | Alembic 迁移（[`alembic/env.py`](alembic/env.py)） |

镜像默认时区为北京时间，见 [`Dockerfile`](Dockerfile) 中 `ENV TZ=Asia/Shanghai`。

## 4. 数据库迁移

表结构：`rrweb_sessions`（会话，含 `is_locked`）+ `rrweb_event_details`（事件分片）。无旧数据回填，DDL 以仓库内 Alembic revision 为准。

### 开发本地（改模型后）

在本服务目录：

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

## 7. 鉴权

所有接口需请求头携带 token，由本服务转发主站 `GET /api/up/auth/verify/` 校验（配置项 `AUTH_VERIFY_URL`，校验协议见主站鉴权文档）。

校验**成功**的结果会按 `AUTH_VERIFY_CACHE_TTL`（默认 8 小时）做进程内短时缓存：同一 token 在有效期内不重复请求主站；失败结果不缓存。多 worker 时各进程缓存独立。

| Header | 说明 |
|--------|------|
| `token` | JWT 或 LongToken |
| `Authorization` | 可选，`JWT <token>` |

示例文档中的 token 统一用 `<your-token>` 占位，勿在文档或仓库中提交真实凭证。

---

## 8. 业务流程

### 8.1 上报（用户端前端）

**触发时机**（事件总线）：

| 事件 | 典型触发场景 | 说明 |
|------|--------------|------|
| `busRrWebStart` | 采购订单详情、平台购物车等 | 传入 `order_plan_id` 开始录制 |
| `busRrWebStop` | 离开订单/方案页等 | 停止录制并上报最后一包 |

**开关**：环境变量 `VITE_ENABLE_RRWEB=1` 时生效（本地默认常为 `0`）。

**录制策略摘要**：

1. `rrweb.record` + `@rrweb/packer` 压缩事件，缓冲到内存数组 `events`
2. 每 **10 秒** 定时 `save()` 上报一包；停止录制时再 `save()` 一次
3. `request_id` / `seq` 放在 **当前页面 JS 模块内存**（与 `order_plan_id`、`rrwebStopFn` 同级），**不写 sessionStorage**；同源多 iframe（浏览器版订单 tab）各有一份模块实例，互不串会话
4. `rrWebStart` 生成新 `request_id`；`rrWebStop` 清空；同一段录制内多包共用该 `request_id`
5. 上报队列串行（`reportQueue`）+ 单调 `seq`，回放按 `seq`（空则按 `id`）
6. 最长录制 **1 小时** 自动停止；后端 BackgroundTasks 异步落库，允许丢片

#### 应用入口：注册总线（`main.js`）

```javascript
// 录屏事件：触发时再动态 import，避免打入首屏包
this.$bus.$on("busRrWebStart", async orderPlanId => {
  const { rrWebStart } = await import("./utils/rrweb.js");
  rrWebStart(orderPlanId);
});
this.$bus.$on("busRrWebStop", async () => {
  const { rrWebStop } = await import("./utils/rrweb.js");
  rrWebStop();
});

// beforeDestroy 中对应 $off
```

#### 录制与上报（`yaocai_frontend/src/utils/rrweb.js`）

以仓库内实现为准：`request_id` / `seq` 为模块内变量（与 `order_plan_id`、`rrwebStopFn` 同级），`rrWebStart` 生成新 `request_id`，`rrWebStop` 清空；不再使用 `sessionStorage` 存会话 ID（仅清理历史遗留键）。

#### HTTP 上报（`src/api/rrweb_api.js`）

```javascript
import axios from "axios";

// 由环境变量注入，勿在仓库中硬编码域名与 token
const API_BASE_URL = import.meta.env.VITE_RRWEB_API_BASE_URL;
const RRWEB_TOKEN = import.meta.env.VITE_RRWEB_TOKEN;

const rrwebClient = axios.create({
  baseURL: API_BASE_URL,
});

rrwebClient.interceptors.request.use(config => {
  config.headers["token"] = RRWEB_TOKEN;
  return config;
});

rrwebClient.interceptors.response.use(
  response => (response.data ? response.data : response),
  error => Promise.reject(error),
);

export const api_rrweb_report = data => {
  return rrwebClient.post("/events", data, {
    headers: { "Content-Type": "application/json" },
  });
};
```

---

### 8.2 列表与回放（管理端前端）

**页面**：管理端录屏列表路由（如 `/#/rrweb`）

**流程**：列表 `GET /events` → 点击「查看」→ `GET /events/detail` → 合并分片 `events` → `rrweb-player` 回放。

#### API 封装（`src/api/rrweb/index.ts`）

```typescript
import axios from 'axios';

const rrwebClient = axios.create({
  baseURL: import.meta.env.VITE_RRWEB_API_BASE_URL,
  timeout: 60000,
});

rrwebClient.interceptors.request.use((config) => {
  config.headers['token'] = import.meta.env.VITE_RRWEB_TOKEN;
  return config;
});

rrwebClient.interceptors.response.use(
  (response) => (response.data != null ? response.data : response),
  (error) => Promise.reject(error)
);

export function apiRrwebList(params?: Record<string, unknown>) {
  return rrwebClient.get('/events', { params });
}

export function apiRrwebDetail(params: Record<string, unknown>) {
  return rrwebClient.get('/events/detail', { params });
}
```

#### 列表与回放页（`src/views/rrweb/index.vue` `<script>`）

```typescript
import { nextTick, onMounted, reactive, ref } from 'vue';
import { ElMessage } from 'element-plus';
import { apiRrwebDetail, apiRrwebList } from '@/api/rrweb';
import { fmtTime } from '@/utils/formatData';
import { rrWebPlayerView } from '@/utils/rrwebPlayer';

const loading = ref(false);
const playerVisible = ref(false);

const filterForm = reactive({
  company_id: '',
  user_id: '',
  order_plan_id: '',
  company_name: '',
});

const tableData = reactive({
  data: [] as Record<string, any>[],
  total: 0,
  page: 1,
  limit: 20,
});

function buildListParams() {
  const params: Record<string, unknown> = {
    page: tableData.page,
    page_size: tableData.limit,
  };
  const companyId = String(filterForm.company_id).trim();
  const userId = String(filterForm.user_id).trim();
  const orderPlanId = String(filterForm.order_plan_id).trim();
  const companyName = String(filterForm.company_name).trim();
  if (companyId !== '') {
    const parsed = Number(companyId);
    if (!Number.isInteger(parsed)) {
      ElMessage.warning('公司ID须为整数');
      return null;
    }
    params.company_id = parsed;
  }
  if (userId !== '') {
    const parsed = Number(userId);
    if (!Number.isInteger(parsed)) {
      ElMessage.warning('用户ID须为整数');
      return null;
    }
    params.user_id = parsed;
  }
  if (orderPlanId !== '') {
    const parsed = Number(orderPlanId);
    if (!Number.isInteger(parsed)) {
      ElMessage.warning('订单ID须为整数');
      return null;
    }
    params.order_plan_id = parsed;
  }
  if (companyName !== '') {
    params.company_name = companyName;
  }
  return params;
}

async function fetchList() {
  const params = buildListParams();
  if (!params) {
    return;
  }
  loading.value = true;
  try {
    const res: any = await apiRrwebList(params);
    tableData.total = Number(res?.count || 0);
    tableData.data = Array.isArray(res?.results) ? res.results : [];
  } catch (error) {
    console.error('获取录屏列表失败:', error);
    ElMessage.error('获取录屏列表失败');
    tableData.data = [];
    tableData.total = 0;
  } finally {
    loading.value = false;
  }
}

function onSearch() {
  tableData.page = 1;
  fetchList();
}

function onReset() {
  filterForm.company_id = '';
  filterForm.user_id = '';
  filterForm.order_plan_id = '';
  filterForm.company_name = '';
  tableData.page = 1;
  fetchList();
}

function onPageSizeChange() {
  tableData.page = 1;
  fetchList();
}

async function openPlayer(row: Record<string, any>) {
  const { company_id, user_id, request_id } = row;
  if (!company_id || !user_id || !request_id) {
    ElMessage.warning('录屏参数不完整，无法回放');
    return;
  }
  playerVisible.value = true;
  try {
    const res: any = await apiRrwebDetail({ company_id, user_id, request_id });
    const segments = Array.isArray(res) ? res : [];
    const allEvents = segments
      .flatMap((item: any) => item?.events || [])
      .sort((a: any, b: any) => (a?.timestamp ?? 0) - (b?.timestamp ?? 0));
    if (!allEvents.length) {
      ElMessage.warning('暂无录屏事件数据');
      return;
    }
    await nextTick();
    rrWebPlayerView('rrweb-player', allEvents);
  } catch (error) {
    console.error('获取录屏详情失败:', error);
    ElMessage.error('获取录屏详情失败');
  }
}

function onPlayerClosed() {
  const el = document.getElementById('rrweb-player');
  if (el) {
    el.innerHTML = '';
  }
}

onMounted(() => {
  fetchList();
});
```

#### 播放器（`src/utils/rrwebPlayer.ts`）

```typescript
import { unpack } from '@rrweb/packer';
import rrwebPlayer from 'rrweb-player';
import 'rrweb-player/dist/style.css';

export function rrWebPlayerView(domId: string, events: unknown[]) {
  const target = document.getElementById(domId);
  if (!target) {
    console.error(`rrweb 播放器容器不存在: #${domId}`);
    return;
  }
  target.innerHTML = '';
  try {
    new rrwebPlayer({
      unpackFn: unpack,
      target,
      props: {
        autoPlay: false,
        events: events as any,
      },
    });
  } catch (error) {
    console.error('rrweb 回放初始化失败:', error);
  }
}
```

---

## 9. 接口说明

基础路径示例：`https://<gateway-host>/api_rrweb`（以实际网关配置为准，下文记为 `{BASE_URL}`）。

### 9.0 健康检查

**接口地址**：`GET {BASE_URL}/ping`

**鉴权**：无需 token

**用途**：容器 / 负载探活，确认进程可响应。

**请求示例**：

```bash
curl -sS "{BASE_URL}/ping"
```

**响应示例**：

```json
{"status": "ok"}
```

### 9.1 上报录屏分片

**接口地址**：`POST {BASE_URL}/events`

**关键参数（Body JSON）**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `request_id` | string | 是 | 本次录制会话 ID（前端 15 位随机串，同一段录制多包共用；存模块内存，不跨 iframe 共享） |
| `record_type` | int | 是 | 录屏类型，`1` = 采购订单录屏 |
| `events` | array | 是 | rrweb 事件数组（pack 压缩后的一包） |
| `seq` | int | 否 | 同一会话内分片序号，前端单调递增；回放优先按此排序 |
| `company_id` | int | 否 | 公司 ID |
| `company_name` | string | 否 | 公司名称 |
| `user_id` | int | 否 | 用户 ID |
| `user_name` | string | 否 | 用户名 |
| `payload` | object | 否 | 扩展数据，采购场景含 `order_plan_id` |

**请求示例**：

```bash
curl -sS -X POST "{BASE_URL}/events" \
  -H "Content-Type: application/json" \
  -H "token: <your-token>" \
  -d '{
    "request_id": "aBcDeFgHiJkLmNo",
    "record_type": 1,
    "seq": 1,
    "company_id": 1,
    "company_name": "示例公司",
    "user_id": 100,
    "user_name": "demo_user",
    "payload": { "order_plan_id": 12345 },
    "events": [{ "type": 4, "data": {}, "timestamp": 1710000000000 }]
  }'
```

**响应示例**：

```json
{
  "status": "accepted",
  "request_id": "aBcDeFgHiJkLmNo",
  "seq": 1
}
```

**字段说明**：

- 鉴权通过后立即返回 `accepted`，分片由 **BackgroundTasks** 异步落库（允许丢片）
- 后端按 `(request_id, company_id, user_id)` **upsert** 会话表，每次上报 **insert** 一条事件分片（含 `seq`）
- 回放顺序：有 `seq` 按 `seq` 升序，`seq` 为空的旧数据再按 `id` 升序

**策略说明**：同一 `request_id` 多次 `POST` 会更新会话元数据并追加 `rrweb_event_details` 行，不会覆盖历史分片；**不会覆盖**已有会话的 `is_locked`。

---

### 9.2 录屏列表

**接口地址**：`GET {BASE_URL}/events`

**关键参数（Query）**：

| 参数 | 类型 | 说明 |
|------|------|------|
| `page` | int | 页码，默认 `1` |
| `page_size` | int | 每页条数，默认 `20` |
| `company_id` | int | 公司 ID，精确匹配 |
| `user_id` | int | 用户 ID，精确匹配 |
| `order_plan_id` | int | 采购订单 ID，匹配 `payload.order_plan_id` |
| `company_name` | string | 公司名，模糊匹配 |

**请求示例**：

```bash
curl -sS "{BASE_URL}/events?page=1&page_size=20&order_plan_id=12345" \
  -H "token: <your-token>"
```

**响应示例**：

```json
{
  "count": 1,
  "results": [
    {
      "id": 1,
      "request_id": "aBcDeFgHiJkLmNo",
      "record_type": 1,
      "is_locked": 0,
      "company_id": 1,
      "company_name": "示例公司",
      "user_id": 100,
      "user_name": "demo_user",
      "payload": { "order_plan_id": 12345 },
      "created_at": "2026-08-29T10:20:00+08:00",
      "updated_at": "2026-08-29T10:25:00+08:00"
    }
  ]
}
```

**字段说明**：

- 列表按 `updated_at` 降序
- `payload.order_plan_id` 即用户端上报的采购订单 ID，管理端「采购订单 ID」筛选用此字段
- `is_locked`：`0` 未锁定，`1` 已锁定（禁止删除与清理）

---

### 9.3 录屏详情（回放数据）

**接口地址**：`GET {BASE_URL}/events/detail`

**关键参数（Query）**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `request_id` | string | 是 | 会话 ID |
| `company_id` | int | 是 | 公司 ID |
| `user_id` | int | 是 | 用户 ID |

**请求示例**：

```bash
curl -sS "{BASE_URL}/events/detail?request_id=aBcDeFgHiJkLmNo&company_id=1&user_id=100" \
  -H "token: <your-token>"
```

**响应示例**：

```json
[
  {
    "id": 10,
    "session_id": 1,
    "seq": 1,
    "events": [{ "type": 4, "data": {}, "timestamp": 1710000000000 }],
    "created_at": "2026-08-29T10:20:10+08:00",
    "updated_at": "2026-08-29T10:20:10+08:00"
  },
  {
    "id": 11,
    "session_id": 1,
    "seq": 2,
    "events": [{ "type": 3, "data": {}, "timestamp": 1710000010000 }],
    "created_at": "2026-08-29T10:20:20+08:00",
    "updated_at": "2026-08-29T10:20:20+08:00"
  }
]
```

**字段说明**：

- 返回该会话下全部分片，排序：`seq` 升序，`seq` 为空时再按 `id` 升序
- 回放端需 `flatMap` 合并各分片 `events`，再按事件 `timestamp` 排序后交给 `rrweb-player`

---

### 9.4 锁定 / 解锁会话

**接口地址**：`PATCH {BASE_URL}/events/{session_id}/lock`

**路径参数**：`session_id` 会话主键 ID

**请求参数（Body JSON）**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `is_locked` | bool | 是 | `true` 锁定，`false` 解锁 |

**请求示例**：

```bash
curl -sS -X PATCH "{BASE_URL}/events/1/lock" \
  -H "Content-Type: application/json" \
  -H "token: <your-token>" \
  -d '{"is_locked": true}'
```

**响应示例**：

```json
{"id": 1, "is_locked": 1}
```

**策略说明**：锁定后不可单条删除、不可被清理接口删除；上报 upsert 不覆盖锁定状态。

---

### 9.5 删除会话

**接口地址**：`DELETE {BASE_URL}/events/{session_id}`

**路径参数**：`session_id` 会话主键 ID

**请求示例**：

```bash
curl -sS -X DELETE "{BASE_URL}/events/1" \
  -H "token: <your-token>"
```

**响应示例**：

```json
{"id": 1, "status": "deleted"}
```

**字段说明**：

- 同步删除 `rrweb_event_details` 中该会话分片
- 已锁定返回 HTTP 400，`msg` 为「已锁定，无法删除」
- 不存在返回 HTTP 404

---

### 9.6 清理过期未锁定会话

**接口地址**：`POST {BASE_URL}/events/cleanup`

**用途**：管理端「清理」按钮；只保留最近六个月数据，**保留锁定回放**（`is_locked=1` 不删）。

**请求示例**：

```bash
curl -sS -X POST "{BASE_URL}/events/cleanup" \
  -H "token: <your-token>"
```

**响应示例**：

```json
{
  "status": "accepted",
  "cutoff_at": "2025-09-10T15:00:00+08:00"
}
```

**字段说明**：

- 鉴权通过后立即返回 `accepted`，清理由 **BackgroundTasks** 异步执行
- `cutoff_at`：清理分界时间（当前时间往前 `30 * 6` 天）
- 实际删除条件：`is_locked = 0` 且 `updated_at < cutoff_at`；已锁定保留

---

## 10. 容器启动

```bash
# 首次 / 变更 Dockerfile 后
docker compose up -d --build

# 仅重启（未改镜像）
docker compose restart
```
