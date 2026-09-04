/**
 * 统一请求封装
 * - 自动带 token
 * - 401 时清掉本地 token 并重新走登录
 * - 统一错误提示
 */
import { BASE_URL, CLOUD_ENV_ID, CLOUD_SERVICE } from "../config";

let refreshing = false;

export function getToken() {
  return uni.getStorageSync("token") || "";
}

export function setToken(token) {
  uni.setStorageSync("token", token);
}

export function clearToken() {
  uni.removeStorageSync("token");
}

function toast(msg) {
  uni.showToast({ title: msg, icon: "none", duration: 2000 });
}

function cloudPath(url, method, data) {
  const path = "/api/v1" + url;
  if (method !== "GET" || !data || Object.keys(data).length === 0) return path;

  const query = Object.entries(data)
    .filter(([, value]) => value !== undefined && value !== null && value !== "")
    .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(value)}`)
    .join("&");
  return query ? `${path}?${query}` : path;
}

function request(method, url, data = {}, _retry = true) {
  return new Promise((resolve, reject) => {
    if (typeof wx === "undefined" || !wx.cloud) {
      toast("当前微信基础库不支持云托管调用");
      reject(new Error("当前微信基础库不支持云托管调用"));
      return;
    }

    wx.cloud.callContainer({
      config: { env: CLOUD_ENV_ID },
      path: cloudPath(url, method, data),
      method,
      data: method === "GET" ? undefined : data,
      header: {
        "X-WX-SERVICE": CLOUD_SERVICE,
        "Content-Type": "application/json",
        Authorization: getToken() ? `Bearer ${getToken()}` : "",
      },
      success: async (res) => {
        const status = res.statusCode;
        if (status === 401) {
          // _retry=false 的二次请求仍 401 时直接失败，避免 无限重登循环
          if (!_retry) return reject(new Error("未登录"));
          if (!refreshing) {
            refreshing = true;
            clearToken();
            try {
              await doLogin();
              refreshing = false;
              // 登录成功后用新 token 重试一次（不再二次重试）
              const retry = await request(method, url, data, false);
              return resolve(retry);
            } catch (e) {
              refreshing = false;
              return reject(new Error("登录失败"));
            }
          }
          return reject(new Error("未登录"));
        }

        if (status >= 200 && status < 300) {
          return resolve(res.data);
        }

        const detail = res.data && (res.data.detail || res.data.message);
        if (detail) toast(typeof detail === "string" ? detail : "请求失败");
        reject(new Error(detail || `HTTP ${status}`));
      },
      fail: (err) => {
        toast("云托管连接失败，请检查服务状态");
        reject(err);
      },
    });
  });
}

export async function doLogin() {
  return new Promise((resolve, reject) => {
    if (typeof wx === "undefined" || !wx.cloud) {
      reject(new Error("当前微信基础库不支持云托管调用"));
      return;
    }

    wx.cloud.callContainer({
      config: { env: CLOUD_ENV_ID },
      path: "/api/v1/auth/login",
      method: "POST",
      header: {
        "X-WX-SERVICE": CLOUD_SERVICE,
        "Content-Type": "application/json",
      },
      // 后端模型仍要求 code 字段；云托管登录实际使用网关注入的 x-wx-openid。
      data: { code: "cloudrun" },
      success: (res) => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          setToken(res.data.token);
          resolve(res.data);
          return;
        }
        const detail = res.data && (res.data.detail || res.data.message);
        reject(new Error(detail || `登录接口异常（HTTP ${res.statusCode}）`));
      },
      fail: reject,
    });
  });
}

/** 上传文件（微信头像等）到后端，返回解析后的 JSON */
function uploadFile(url, filePath, name = "file") {
  return new Promise((resolve, reject) => {
    uni.uploadFile({
      url: BASE_URL + url,
      filePath,
      name,
      header: { Authorization: getToken() ? `Bearer ${getToken()}` : "" },
      success: (res) => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          try {
            resolve(JSON.parse(res.data));
          } catch (e) {
            resolve(res.data);
          }
        } else {
          let msg = "上传失败";
          try {
            const d = JSON.parse(res.data);
            msg = d.detail || d.message || msg;
          } catch (e) {
            /* ignore */
          }
          toast(typeof msg === "string" ? msg : "上传失败");
          reject(new Error(msg));
        }
      },
      fail: (err) => {
        toast("网络连接失败，请检查后端是否启动");
        reject(err);
      },
    });
  });
}

export const http = {
  get: (url, data) => request("GET", url, data),
  post: (url, data) => request("POST", url, data),
  put: (url, data) => request("PUT", url, data),
  del: (url) => request("DELETE", url),
};

export { BASE_URL, toast, uploadFile };
