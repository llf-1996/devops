## rrweb
rrweb 录制与回放功能说明

### 简介
本项目使用 rrweb 实现了前端操作录制和回放功能，用于记录用户在页面上的行为，以便于后续分析或调试。
### 功能模块
以下为 rrweb.js 文件中主要实现的功能模块：
1. 录制开始 rrWebStart(current_order_plan_id)
   * 功能：初始化录制流程。
   * 参数：
      * current_order_plan_id：当前订单计划 ID，用于标识录制上下文。
   * 逻辑说明：
      * 如果已存在录制实例，则先停止旧的录制。
      * 通过 rrweb.record 启动录制，将事件通过 emit 存入 events 数组。
      * 设置 1 小时超时自动停止录制。
2. 录制停止 rrWebStop()
   * 功能：停止录制并清理相关资源。
   * 逻辑说明：
     * 调用 rrwebStopFn() 停止录制。
     * 调用 save() 方法上传录制数据。
     * 清除定时器和相关状态。
3. 播放器 rrWebPlayerView(domId, events)
   * 功能：初始化回放播放器。
   * 参数：
     * domId：播放器容器的 DOM ID。
     * events：录制的事件数据。
   * 逻辑说明：
     * 使用 rrwebPlayer 创建播放器实例。
     * 支持手动播放录制的事件。
### 依赖
   * rrweb: 用于录制用户行为。
   * @rrweb/packer: 用于打包录制数据。
   * @rrweb-player: 用于回放录制数据。
   * api_rrweb_report: 自定义 API 接口，用于上传录制数据。
```bash
npm install rrweb rrweb-player @rrweb/packer
```

### 示例代码
```js
// 启动录制
import { rrWebStart, rrWebStop, rrWebPlayerView } from "./rrweb.js";
rrWebStart("order_plan_123");

// 停止录制
rrWebStop();

// 回放录制数据
rrWebPlayerView("player-container", recordedEvents);
```
