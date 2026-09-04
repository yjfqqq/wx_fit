// 深色模式 · 单一真值 + 自动跟随系统 + 手动开关 + 持久化。
// 设计令牌全部用 CSS 变量，深色只需在根节点挂 .dark 类重定义令牌，无需两套样式表。
import { ref } from "vue";

function getSystemTheme() {
  try {
    const info = uni.getSystemInfoSync();
    return info && info.theme === "dark" ? "dark" : "light";
  } catch (e) {
    return "light";
  }
}

const stored = (() => {
  try {
    return uni.getStorageSync("fit_theme");
  } catch (e) {
    return "";
  }
})();

export const theme = ref(stored || getSystemTheme() || "light");

function toggleClass(el, isDark) {
  if (!el || !el.classList || typeof el.classList.toggle !== "function") return;
  el.classList.toggle("dark", isDark);
}

export function applyTheme() {
  const isDark = theme.value === "dark";
  // H5：根节点挂类
  try {
    if (typeof document !== "undefined" && document.documentElement) {
      document.documentElement.classList.toggle("dark", isDark);
    }
  } catch (e) {}
  // mp-weixin / 各端：给当前所有页面根节点挂类，CSS 变量沿继承链下发给全部子节点
  try {
    const pages = typeof getCurrentPages === "function" ? getCurrentPages() : [];
    pages.forEach((p) => {
      const el = p && (p.$el || (p.$vm && p.$vm.$el));
      toggleClass(el, isDark);
    });
  } catch (e) {}
  // 同步原生导航栏配色（frontColor 仅支持 #ffffff / #000000）
  try {
    uni.setNavigationBarColor({
      frontColor: isDark ? "#ffffff" : "#000000",
      backgroundColor: isDark ? "#0E1512" : "#F6F8F7",
      fail: () => {},
    });
  } catch (e) {}
}

export function setTheme(t) {
  theme.value = t;
  try {
    uni.setStorageSync("fit_theme", t);
  } catch (e) {}
  applyTheme();
}

export function initTheme() {
  applyTheme();
}
