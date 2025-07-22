import axios from "axios";

const API_BASE_URL = "http://127.0.0.1:8000";

// 创建一个新的Axios实例
const API_SPIDER = axios.create({
  baseURL: API_BASE_URL,
});

// 添加请求拦截器
API_SPIDER.interceptors.request.use(
  function (config) {
    if (localStorage.getItem("token")) {
      config.headers["token"] = localStorage.getItem("token");
    }
    config.disable_error_tip = false;
    return config;
  },
  async function (error) {
    console.error("interceptors.response(error): ", error);
    return Promise.reject(error);
  },
);

// 添加响应拦截器
API_SPIDER.interceptors.response.use(
  function (response) {
    // 2xx 范围内的状态码都会触发该函数。
    // 对响应数据做点什么
    return response.data ? response.data : response;
  },
  function (error) {
    // 超出 2xx 范围的状态码都会触发该函数。
    // 对响应错误做点什么
    console.error("interceptors.response(error): ", error);
    return Promise.reject(error);
  },
);


// 上报录屏数据
export const api_rrweb_report = data => {
  return API_SPIDER.post("/events", data, {
    headers: {
      "Content-Type": "application/json",
    },
  });
}

// 录屏列表
export const api_rrweb_list = params => {
  return API_SPIDER.get("/events", { params: params });
}

// 录屏详情
export const api_rrweb_detail = params => {
  return API_SPIDER.get("/events/detail", { params: params });
}
