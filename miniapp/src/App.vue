<script setup>
import { onLaunch } from "@dcloudio/uni-app";
import { useUserStore } from "@/store/user";
import { initTheme } from "@/utils/theme";
import { CLOUD_ENV_ID } from "@/config";

onLaunch(() => {
  const user = useUserStore();
  user.restore();
  initTheme(); // 跟随系统 / 已保存的手动偏好，挂 .dark 类

  // 微信云托管初始化；后续登录通过 callContainer 获取可信 openid。
  if (typeof wx !== "undefined" && wx.cloud) {
    wx.cloud.init({ env: CLOUD_ENV_ID });
  }
});
</script>

<style lang="scss">
@import "./styles/components.css";

/* ============================================================
   设计系统 v3 ·「静水 Still Water」
   ============================================================
   全站唯一的颜色与空间来源。所有页面只允许引用这里的令牌，
   禁止出现 #fff / #e6efea 这类字面量。

   空间尺度（8 个值，其它一律不用）：
     --pad-x      32rpx   页面左右边距
     --gap-card   24rpx   卡片与卡片之间
     --pad-card   32rpx   卡片内边距
     --gap-block  40rpx   卡内区块（分隔线上下）
     --gap-field  24rpx   表单字段之间
     --gap-label  12rpx   标签 → 输入框
     --gap-item   16rpx   列表项之间
     --hit-min    88rpx   最小触摸目标
   ============================================================ */
page {
  /* ---------- 表面 ---------- */
  --bg: #f6f8f7;
  --card: #ffffff;
  --surface-2: #eef2f0;
  --line: #e1e8e4;
  --line-strong: #cbd6cf;

  /* ---------- 文字层级 ---------- */
  --ink: #0f2419;    /* 标题 / 主数字       16.32:1 */
  --ink-2: #3d5a4c;  /* 正文                7.59:1  */
  --ink-3: #5a7568;  /* 说明 / 单位 / 占位   5.02:1  */
  --ink-4: #5a7568;  /* 极弱文字（并入 ink-3，保证可读） */

  /* ---------- 品牌 ---------- */
  --brand: #06794c;        /* 白字 5.46:1 · 作文字 5.46:1 */
  --brand-deep: #046a43;   /* 按压态        6.67:1 */
  --brand-light: #0b8f5b;
  --brand-tint: #def3e7;   /* 浅绿底，配 --brand 文字 4.70:1 */
  --grad-brand: linear-gradient(135deg, #078157 0%, #04603b 100%);
  --grad-blue: linear-gradient(135deg, #3d8bc9 0%, #2a6a9e 100%);
  --on-brand: #ffffff;

  /* ---------- 语义色（文字 / 填充 / 浅底 三档） ---------- */
  --amber: #8a5a00;      --amber-fill: #b8791c;  --amber-tint: #fff4dc;
  --red: #a8322a;        --red-fill: #d04538;    --red-tint: #fdecea;
  --blue: #2a6a9e;       --blue-fill: #3d8bc9;   --blue-tint: #e5f0fa;

  /* ---------- 空间尺度 ---------- */
  --pad-x: 32rpx;
  --gap-card: 24rpx;
  --pad-card: 32rpx;
  --gap-block: 40rpx;
  --gap-field: 24rpx;
  --gap-label: 12rpx;
  --gap-item: 16rpx;
  --hit-min: 88rpx;

  /* ---------- 圆角 ---------- */
  --r-lg: 32rpx;
  --r-md: 24rpx;
  --r-sm: 16rpx;
  --r-pill: 999rpx;

  /* ---------- 阴影：靠描边分层，阴影只做极轻辅助 ---------- */
  --shadow-card: 0 2rpx 4rpx rgba(15, 36, 25, 0.04);
  --shadow-float: 0 8rpx 24rpx rgba(15, 36, 25, 0.1);
  --shadow-btn: 0 12rpx 32rpx rgba(6, 121, 76, 0.24);

  /* ---------- 动效 ---------- */
  --e-out: cubic-bezier(0.22, 1, 0.36, 1);
  --d-fast: 140ms;
  --d-base: 240ms;
  --d-slow: 420ms;

  background: var(--bg);
  color: var(--ink);
  font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue",
    "PingFang SC", "Microsoft YaHei", sans-serif;
  font-size: 28rpx;
  line-height: 1.5;
  -webkit-font-smoothing: antialiased;
}

/* ============================================================
   深色模式 ·「夜航」
   只在根节点重定义令牌，全部子节点沿 CSS 变量继承，无需两套样式表。
   表面三级抬升（#0E1512 → #16211C → #1D2A24），品牌绿提到 #4ECB8B。
   ============================================================ */
page.dark,
.dark {
  --bg: #0e1512;
  --card: #16211c;
  --surface-2: #1d2a24;
  --line: #26352e;
  --line-strong: #34453c;

  --ink: #e8efea;    /* 标题 / 主数字  15.83:1 AAA */
  --ink-2: #a9bdb2;  /* 正文            9.35:1 AAA */
  --ink-3: #87998f;  /* 说明 / 单位     6.15:1 AA  */
  --ink-4: #87998f;  /* 极弱文字并入 ink-3，保可读 */

  --brand: #4ecb8b;        /* 深色底 9.02:1 AAA */
  --brand-deep: #2e9e69;   /* 按压态 */
  --brand-light: #6fe0a8;
  --brand-tint: #163a2c;   /* 深绿底，配浅绿文字 */
  --grad-brand: linear-gradient(135deg, #4ecb8b 0%, #2e9e69 100%);
  --grad-blue: linear-gradient(135deg, #5aaae0 0%, #3d8bc9 100%);
  --on-brand: #0e1512;     /* 浅绿按钮配深色文字 9.02:1 */

  /* 语义色：深色下降饱和、提亮度 */
  --amber: #e0b256;  --amber-fill: #c9923a;  --amber-tint: #2e2410;
  --red: #e8726a;    --red-fill: #d04538;    --red-tint: #2e1715;
  --blue: #7fb8e0;   --blue-fill: #3d8bc9;   --blue-tint: #14222e;

  --shadow-card: 0 2rpx 8rpx rgba(0, 0, 0, 0.4);
  --shadow-float: 0 8rpx 24rpx rgba(0, 0, 0, 0.5);
  --shadow-btn: 0 12rpx 32rpx rgba(0, 0, 0, 0.5);

  background: var(--bg);
  color: var(--ink);
}

/* 覆盖 uni-app <button> 的默认边框与内边距 */
button {
  padding: 0;
  margin: 0;
  background: transparent;
  line-height: normal;
  font-size: inherit;
}
button::after {
  border: none;
}
</style>
