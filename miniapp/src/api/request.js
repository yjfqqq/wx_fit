/**
 * 统一请求封装
 * - 自动带 token
 * - 401 时清掉本地 token 并重新走登录
 * - 统一错误提示
 */
import { BASE_URL } from "../config";

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

function request(method, url, data = {}, _retry = true) {
  return new Promise((resolve, reject) => {
    uni.request({
      url: BASE_URL + url,
      method,
      data,
      header: {
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
        toast("网络连接失败，请检查后端是否启动");
        reject(err);
      },
    });
  });
}

export async function doLogin() {
  return new Promise((resolve, reject) => {
    uni.login({
      provider: "weixin",
      success: async (loginRes) => {
        try {
          const res = await new Promise((ok, no) => {
            uni.request({
              url: BASE_URL + "/auth/login",
              method: "POST",
              data: { code: loginRes.code || "mock" },
              header: { "Content-Type": "application/json" },
              success: (r) =>
                r.statusCode < 300 ? ok(r.data) : no(new Error("登录接口异常")),
              fail: no,
            });
          });
          setToken(res.token);
          resolve(res);
        } catch (e) {
          reject(e);
        }
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
