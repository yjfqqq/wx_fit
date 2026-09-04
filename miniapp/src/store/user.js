import { defineStore } from "pinia";
import { authApi } from "@/api";
import { clearToken, doLogin, getToken } from "@/api/request";
import { BASE_URL } from "@/config";

const staticRoot = BASE_URL.replace(/\/api\/v1\/?$/, "");

export const useUserStore = defineStore("user", {
  state: () => ({
    token: "",
    profile: null,
    goal: null,
    // 头像的本地临时路径（downloadFile 下载后），避免 <image> 直接加载 http 网络图失败
    avatarLocal: "",
  }),
  getters: {
    isLogin: (s) => !!s.token,
    displayName: (s) => s.profile?.nickname || "运动达人",
    avatarFullUrl: (s) => {
      const u = s.profile?.avatar_url;
      if (!u) return "";
      if (u.startsWith("http")) return u;
      return staticRoot + u;
    },
    // 展示用头像地址：优先本地临时路径，兜底回网络 URL
    avatarSrc: (s) => s.avatarLocal || (() => {
      const u = s.profile?.avatar_url;
      if (!u) return "";
      return u.startsWith("http") ? u : staticRoot + u;
    })(),
  },
  actions: {
    restore() {
      this.token = getToken();
    },
    async ensureLogin() {
      if (!this.token) {
        await doLogin();
        this.token = getToken();
      }
      if (!this.profile) {
        await this.loadProfile();
      }
    },
    async loadProfile() {
      try {
        this.profile = await authApi.me();
        this.goal = await authApi.getGoal();
      } catch (e) {
        /* 失败不阻塞页面 */
      }
    },
    async saveProfile(data) {
      this.profile = await authApi.updateProfile(data);
      return this.profile;
    },
    async saveGoal(data) {
      this.goal = await authApi.setGoal(data);
    },
    /**
     * 用 downloadFile 把头像网络图下载为本地临时路径，
     * 供 <image> 直接引用；加载失败静默保留网络地址兜底。
     */
    async loadAvatarLocal() {
      const net = this.avatarFullUrl;
      if (!net || net.startsWith("wxfile://")) return;
      // 短缓存：同一网络地址只下载一次，避免每次进入都重新下载
      if (this._lastAvatarNet === net) return;
      try {
        const r = await new Promise((resolve, reject) => {
          uni.downloadFile({
            url: net,
            header: {
              Authorization: getToken() ? `Bearer ${getToken()}` : "",
            },
            success: resolve,
            fail: reject,
          });
        });
        if (r.statusCode >= 200 && r.statusCode < 300 && r.tempFilePath) {
          this.avatarLocal = r.tempFilePath;
          this._lastAvatarNet = net;
        }
      } catch (e) {
        /* 下载失败不阻塞页面，头像走网络地址兜底 */
      }
    },
    resetAvatarLocal() {
      this.avatarLocal = "";
      this._lastAvatarNet = "";
    },
    logout() {
      clearToken();
      this.token = "";
      this.profile = null;
      this.goal = null;
      this.avatarLocal = "";
      this._lastAvatarNet = "";
    },
  },
});
