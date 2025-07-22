import * as rrweb from "rrweb";
import { pack, unpack } from "@rrweb/packer";
import rrwebPlayer from 'rrweb-player';

import { api_rrweb_report } from "@/api/rrweb_api.js";


let request_id = sessionStorage.getItem("rrweb_request_id");
let order_plan_id, events = [], rrwebStopFn = null, timer = null, userInfo = {};


function _getNow() {
  const date = new Date();
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  const seconds = String(date.getSeconds()).padStart(2, '0');
  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
}


// 录制开始
function rrWebStart(current_order_plan_id) {
  console.log("rrWebStart...");
  if (import.meta.env.VITE_ENABLE_RRWEB === "0") {
    console.info("当前环境不支持录制，请检查环境变量 VITE_ENABLE_RRWEB")
    return;
  }
  order_plan_id = current_order_plan_id;
  if (rrwebStopFn) {
    rrWebStop();
  }
  rrwebStopFn = rrweb.record({
    packFn: pack,
    emit(event) {
      events.push(event);
    },
    // sampling: {
    //   // 不录制鼠标移动事件
    //   mousemove: false,
    //   // 不录制鼠标交互事件
    //   mouseInteraction: false,
    //   // 设置滚动事件的触发频率
    //   scroll: 150, // 每 150ms 最多触发一次
    //   // set the interval of media interaction event
    //   media: 800,
    //   // 设置输入事件的录制时机
    //   input: "last", // 连续输入时，只录制最终值
    // },
  });
  // 定时上传录屏数据
  timer = setInterval(save, 10 * 1000);
  setTimeout(rrWebStop, 60 * 60 * 1000);  // 最多录制1小时
}

// 录制停止
function rrWebStop() {
  console.log("rrWebStop...");
  if (import.meta.env.VITE_ENABLE_RRWEB === "0") {
    console.info("当前环境不支持录制，请检查环境变量 VITE_ENABLE_RRWEB")
    return;
  }
  if (rrwebStopFn) {
    save();
    rrwebStopFn(); // 调用这个方法就停止了
    rrwebStopFn = null;
    sessionStorage.removeItem("rrweb_request_id");
    request_id = null;
  }
  if (timer) {
    clearInterval(timer);
    timer = null;
  }
}

function save() {
  if (events.length === 0) {
    return;
  }
  if (!request_id) {
    request_id = getUuid();
    sessionStorage.setItem("rrweb_request_id", request_id);
  }
  if (Object.keys(userInfo).length === 0) {
    let rawInfo = localStorage.getItem("userInfo") || "{}";
    rawInfo = JSON.parse(rawInfo);
    userInfo = {
      company_id: rawInfo.company_id,
      company_name: rawInfo.company_name,
      user_id: rawInfo.id,
      user_name: rawInfo.username,
    }
  }
  const body = {
    ...userInfo,
    events,
    request_id: request_id,
    request_at: _getNow(), // 格式：2025-04-05T12:34:56.789Z
    payload: {
      order_plan_id,
    },
  };
  events = [];
  api_rrweb_report(body)
}

function getUuid() {
  let length = 15, result = "";
  let characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
  for (let i = 0; i < length; i++) {
    let randomIndex = Math.floor(Math.random() * characters.length);
    result += characters.charAt(randomIndex);
  }
  return result;

}

const rrWebPlayerView = (domId, events) => {
  if (import.meta.env.VITE_ENABLE_RRWEB === "0") {
    console.info("当前环境不支持录制，请检查环境变量 VITE_ENABLE_RRWEB")
    return;
  }
  try {
    new rrwebPlayer({
      unpackFn: unpack,
      target: document.getElementById(domId),
      props: {
        autoPlay: false,
        events: events,
      },
    })
  } catch (error) {
    console.error(error);
  }
}

export { rrWebStop, rrWebStart, rrWebPlayerView };
