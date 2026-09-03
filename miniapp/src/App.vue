<script setup>
import { onLaunch } from "@dcloudio/uni-app";
import { useUserStore } from "@/store/user";

onLaunch(() => {
  const user = useUserStore();
  user.restore();
});
</script>

<style lang="scss">
/* ============================================================
   设计系统 · 活力青绿 / 治愈自然 (Vivid Emerald)
   全部页面共享的 Design Tokens —— 修改这里即可全局换肤
   ============================================================ */
page {
  /* 基础底色 */
  --bg: #f2f7f3;
  --card: #ffffff;

  /* 文字层级 */
  --ink: #163c2f; /* 标题 / 主数字 */
  --ink-2: #5b7467; /* 正文 */
  --ink-3: #8da698; /* 次要说明 */
  --ink-4: #b6c7bd; /* 占位符 / 弱化 */
  --line: #e4ede6; /* 分隔线 / 描边 */

  /* 品牌主色(翡翠绿) */
  --brand: #0e9e68; /* 主操作 / 达标 */
  --brand-deep: #0b7a50; /* 按压态 / 强调文字 */
  --brand-light: #2bc58e; /* 渐变亮端 */
  --brand-tint: #e2f5ea; /* 浅绿底(选中 / 标签) */
  --grad-brand: linear-gradient(135deg, #22bd85 0%, #0d9a63 100%);

  /* 辅助色 */
  --amber: #d9962f; /* 提醒 / 未计热量 / 待办 */
  --amber-tint: #fcf0da;
  --red: #e85447; /* 超标 / 上升 / 删除 */
  --red-tint: #fdeae6;
  --blue: #4e9fe0; /* 运动消耗 / 数据蓝 */
  --blue-tint: #e8f3fc;

  /* 圆角与投影 */
  --r-lg: 32rpx;
  --r-md: 24rpx;
  --r-sm: 18rpx;
  --shadow-card: 0 10rpx 30rpx rgba(20, 94, 62, 0.06);
  --shadow-btn: 0 12rpx 24rpx rgba(14, 158, 104, 0.24);

  background: var(--bg);
  color: var(--ink);
  font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue",
    "PingFang SC", "Microsoft YaHei", sans-serif;
  font-size: 28rpx;
  line-height: 1.5;
  -webkit-font-smoothing: antialiased;
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
