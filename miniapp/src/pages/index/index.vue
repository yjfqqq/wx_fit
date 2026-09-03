<template>
  <view class="page">
    <!-- ============ 沉浸式渐变头部 ============ -->
    <view class="hero">
      <view class="hero-bg" />
      <view class="hero-inner">
        <view class="greet">
          <text class="title">{{ greetTitle }}</text>
          <view class="greet-sub">
            <text class="slogan">记录每一天,看见更好的自己</text>
            <text class="date-chip">{{ dateText }}</text>
          </view>
        </view>

        <!-- 未授权微信时的引导入口 -->
        <view class="wx-entry" v-if="!user.hasWxProfile" @click="goAuth">
          <view class="wx-entry-l">
            <text class="wx-entry-ico">👤</text>
            <text class="wx-entry-txt">用微信头像昵称登录,记录更贴心</text>
          </view>
          <text class="wx-entry-btn">去授权</text>
        </view>

        <!-- 体重卡片(悬浮于渐变上) -->
        <view class="w-card">
          <view class="w-top">
            <view class="w-title">
              <text class="wt-label">当前体重</text>
              <text class="pill" :class="bmiPillClass" v-if="bmi">
                BMI {{ bmi }} · {{ bmiLevel }}
              </text>
            </view>

            <view class="w-main">
              <view class="w-num">
                <text class="num">{{ currentWeight ?? "--" }}</text>
                <text class="unit">kg</text>
              </view>

              <view class="w-side" v-if="targetWeight">
                <text class="side-label">距目标</text>
                <view class="side-val">
                  <text class="side-num" :class="{ good: gap != null && gap <= 0 }">
                    {{ gap == null ? "--" : gap > 0 ? gap.toFixed(1) : "已达成" }}
                  </text>
                  <text class="side-unit" v-if="gap != null && gap > 0">kg</text>
                </view>
              </view>
              <view class="w-side" v-else>
                <text class="side-label">还没设目标</text>
                <navigator url="/pages/profile/goal" class="link-btn">去设置</navigator>
              </view>
            </view>
          </view>

          <view class="progress" v-if="progress !== null">
            <view class="bar">
              <view class="fill" :style="{ width: progress * 100 + '%' }" />
            </view>
            <view class="bar-ends">
              <text>{{ startWeight ?? "?" }} kg 起</text>
              <text>目标 {{ targetWeight }} kg</text>
            </view>
          </view>
        </view>
      </view>
    </view>

    <!-- ============ 今日热量 ============ -->
    <view class="card">
      <view class="card-head">
        <view class="head-l">
          <text class="head-dot c-green" />
          <text class="card-title">今日热量</text>
        </view>
        <text class="tag amber" v-if="unknownCount">
          {{ unknownCount }} 条未计热量
        </text>
      </view>

      <view class="ring-row">
        <view class="ring" :style="ringStyle">
          <view class="ring-inner">
            <text class="ring-num">{{ remainingText }}</text>
            <text class="ring-label">还可摄入</text>
          </view>
        </view>

        <view class="ring-info">
          <view class="info-line">
            <view class="kpi">
              <view class="dot in" />
              <text>摄入</text>
            </view>
            <text class="info-num">{{ intake }} kcal</text>
          </view>
          <view class="info-line">
            <view class="kpi">
              <view class="dot out" />
              <text>消耗</text>
            </view>
            <text class="info-num">{{ burn }} kcal</text>
          </view>
          <view class="info-line">
            <view class="kpi">
              <view class="dot budget" />
              <text>预算</text>
            </view>
            <text class="info-num">{{ budgetText }}</text>
          </view>
        </view>
      </view>

      <view class="macros">
        <view class="macro">
          <view class="macro-bar p" :style="proteinBar" />
          <text class="mv">{{ protein }}g</text>
          <text class="ml">蛋白质</text>
        </view>
        <view class="macro">
          <view class="macro-bar c" :style="carbsBar" />
          <text class="mv">{{ carbs }}g</text>
          <text class="ml">碳水</text>
        </view>
        <view class="macro">
          <view class="macro-bar f" :style="fatBar" />
          <text class="mv">{{ fat }}g</text>
          <text class="ml">脂肪</text>
        </view>
      </view>
    </view>

    <!-- ============ 今日任务 ============ -->
    <view class="card">
      <view class="card-head">
        <view class="head-l">
          <text class="head-dot c-amber" />
          <text class="card-title">今日任务</text>
        </view>
        <text class="task-count">{{ doneCount }}/{{ tasks.length }} 已完成</text>
      </view>

      <view class="task" v-for="t in tasks" :key="t.key">
        <view class="task-box" :class="{ done: t.done }">
          <text v-if="t.done" class="tick">✓</text>
        </view>
        <text class="task-text" :class="{ done: t.done }">{{ t.text }}</text>
        <view class="task-action" v-if="!t.done" @click="goRecord(t.tab)">去记录</view>
      </view>
    </view>

    <!-- ============ 本周概览 ============ -->
    <view class="card">
      <view class="card-head">
        <view class="head-l">
          <text class="head-dot c-blue" />
          <text class="card-title">本周打卡</text>
        </view>
      </view>
      <view class="week-grid">
        <view v-for="d in week" :key="d.date" class="week-day">
          <text class="wd-label" :class="{ on: d.active }">{{ d.label }}</text>
          <view class="wd-badge" :class="{ on: d.active }">
            <text v-if="d.active" class="wd-check">✓</text>
          </view>
        </view>
      </view>
      <view class="week-sum">
        近 7 天记录了
        <text class="hl">{{ weekCount }}</text>
        天,体重变化
        <text class="hl">{{ weekChangeText }}</text>
      </view>
    </view>

    <view class="disclaimer">
      本工具仅用于个人数据记录,食物热量为估算值,不构成医疗建议
    </view>
  </view>
</template>

<script setup>
import { ref, computed } from "vue";
import { onShow } from "@dcloudio/uni-app";
import { statsApi } from "@/api";
import { useUserStore } from "@/store/user";
import { today, niceDate, addDays, weekdayCN } from "@/utils/date";

const user = useUserStore();
const summary = ref(null);
const plan = ref(null);
const overview = ref(null);
const week = ref([]);

const dateText = computed(() => niceDate(today()));
const greetText = computed(() => {
  const h = new Date().getHours();
  if (h < 6) return "夜深了";
  if (h < 11) return "早上好";
  if (h < 14) return "中午好";
  if (h < 18) return "下午好";
  return "晚上好";
});
// 带昵称的问候,如"早上好,小明"
const greetTitle = computed(() => {
  const n = user.displayName;
  const isDefault = n === "微信用户" || n === "运动达人" || n === "测试用户";
  return isDefault ? greetText.value : `${greetText.value},${n}`;
});

// 优先显示今天称的体重；今天没称则回退到最近一次记录（overview.current_weight）
const currentWeight = computed(() => {
  if (summary.value?.weight_kg != null) return Number(summary.value.weight_kg);
  if (overview.value?.current_weight != null)
    return Number(overview.value.current_weight);
  return null;
});
const targetWeight = computed(() =>
  overview.value?.target_weight != null ? Number(overview.value.target_weight) : null
);
const startWeight = computed(() =>
  overview.value?.start_weight != null ? Number(overview.value.start_weight) : null
);
const gap = computed(() =>
  currentWeight.value != null && targetWeight.value != null
    ? currentWeight.value - targetWeight.value
    : null
);
const progress = computed(() => plan.value?.progress ?? null);
const bmi = computed(() => plan.value?.bmi ?? null);
const bmiLevel = computed(() => plan.value?.bmi_level ?? "");
const bmiPillClass = computed(() => {
  const l = bmiLevel.value;
  if (l.includes("肥胖")) return "danger";
  if (l.includes("偏胖") || l.includes("超重")) return "amber";
  if (l.includes("偏瘦")) return "blue";
  return "green";
});

const intake = computed(() => Math.round(summary.value?.intake_kcal ?? 0));
const burn = computed(() => Math.round(summary.value?.burn_kcal ?? 0));
const protein = computed(() => Math.round(summary.value?.protein ?? 0));
const carbs = computed(() => Math.round(summary.value?.carbs ?? 0));
const fat = computed(() => Math.round(summary.value?.fat ?? 0));
const unknownCount = computed(() => summary.value?.unknown_calorie_count ?? 0);
const budget = computed(() =>
  summary.value?.budget_kcal != null ? Math.round(summary.value.budget_kcal) : null
);
const budgetText = computed(() => (budget.value ? budget.value + " kcal" : "先填资料"));
const remainingText = computed(() => {
  if (!budget.value) return "--";
  const rest = budget.value - intake.value;
  return rest > 0 ? String(rest) : "超 " + Math.abs(rest);
});

const ringStyle = computed(() => {
  const pct = budget.value
    ? Math.min(intake.value / budget.value, 1.5) / 1.5 * 100
    : 0;
  const over = budget.value && intake.value > budget.value;
  const color = over ? "#e85447" : "var(--brand)";
  return {
    background: `conic-gradient(${color} ${pct}%, #e6efea ${pct}%)`,
  };
});

// 三大营养素迷你进度条(占当前摄入热量的参考比例,封顶 100%)
const maxMacro = computed(() =>
  Math.max(1, protein.value, carbs.value, fat.value)
);
const proteinBar = computed(() => ({
  width: (protein.value / maxMacro.value) * 100 + "%",
}));
const carbsBar = computed(() => ({
  width: (carbs.value / maxMacro.value) * 100 + "%",
}));
const fatBar = computed(() => ({
  width: (fat.value / maxMacro.value) * 100 + "%",
}));

const tasks = computed(() => {
  const s = summary.value;
  return [
    { key: "w", tab: 0, text: "记录今天的体重", done: !!(s && s.weight_kg) },
    { key: "m", tab: 1, text: "记录今天吃了什么", done: !!(s && s.meal_count > 0) },
    { key: "e", tab: 2, text: "动一动,记录运动", done: !!(s && s.exercise_count > 0) },
  ];
});
const doneCount = computed(() => tasks.value.filter((t) => t.done).length);

const weekCount = computed(() => week.value.filter((d) => d.active).length);
const weekChangeText = computed(() => {
  const r = overview.value?.weekly_rate;
  if (r == null) return "数据不足";
  const v = Number(r);
  if (Math.abs(v) < 0.1) return "基本持平";
  return (v > 0 ? "+" : "") + v.toFixed(2) + " kg/周";
});

function goRecord(tab) {
  uni.setStorageSync("record_tab", tab);
  uni.switchTab({ url: "/pages/record/record" });
}

function goAuth() {
  uni.navigateTo({ url: "/pages/profile/wx-auth" });
}

async function load() {
  try {
    await user.ensureLogin();
    // 强制刷新用户资料,保证昵称/头像即时更新(授权页返回后生效)
    await user.loadProfile();
    const d = today();
    const [s, p, o] = await Promise.all([
      statsApi.summary(d),
      statsApi.plan(),
      statsApi.overview(),
    ]);
    summary.value = s;
    plan.value = p;
    overview.value = o;

    // 近 7 天打卡情况
    const cal = await statsApi.calendar(d.slice(0, 7));
    const map = {};
    (cal || []).forEach((i) => (map[i.date] = i));
    const list = [];
    for (let i = 6; i >= 0; i--) {
      const date = addDays(d, -i);
      const item = map[date];
      list.push({
        date,
        label: weekdayCN(date),
        active: !!(item && (item.has_meal || item.has_weight || item.has_exercise)),
      });
    }
    week.value = list;

    // 首次进入:尚未授权微信资料时,顶部问候下出现"微信授权"入口提示
    if (!user.hasWxProfile && !uni.getStorageSync("wx_auth_hint_shown")) {
      uni.setStorageSync("wx_auth_hint_shown", 1);
      uni.showToast({ title: "未授权微信,去「我的」页绑定吧", icon: "none" });
    }
  } catch (e) {
    console.error(e);
  }
}

onShow(load);
</script>

<style scoped lang="scss">
/* ============ 沉浸式渐变头部 ============ */
.hero {
  position: relative;
  background: linear-gradient(160deg, #14b97e 0%, #0da267 55%, #0b8f59 100%);
  padding-top: var(--status-bar-height);
  padding-bottom: 120rpx;
  overflow: hidden;
}
.page {
  background: linear-gradient(180deg, #e8f5ee 0%, var(--bg) 200rpx);
}
.hero-bg {
  position: absolute;
  right: -120rpx;
  top: -140rpx;
  width: 440rpx;
  height: 440rpx;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.18) 0%, rgba(255, 255, 255, 0) 70%);
  pointer-events: none;
}
.hero-inner {
  position: relative;
  padding: 24rpx 32rpx 0;
}
.greet {
  margin-top: 44rpx;
  .title {
    display: block;
    font-size: 52rpx;
    font-weight: 600;
    color: #fff;
    letter-spacing: 2rpx;
  }
  .greet-sub {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-top: 10rpx;
  }
  .date-chip {
    font-size: 24rpx;
    color: rgba(255, 255, 255, 0.92);
    background: rgba(255, 255, 255, 0.18);
    border: 1rpx solid rgba(255, 255, 255, 0.3);
    padding: 10rpx 24rpx;
    border-radius: 999rpx;
    margin-left: 20rpx;
    flex-shrink: 0;
  }
}
.slogan {
  font-size: 26rpx;
  color: rgba(255, 255, 255, 0.78);
  flex: 1;
  min-width: 0;
}

/* 微信授权引导 */
.wx-entry {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 26rpx;
  background: rgba(255, 255, 255, 0.16);
  border: 1rpx solid rgba(255, 255, 255, 0.28);
  border-radius: 22rpx;
  padding: 18rpx 24rpx;
}
.wx-entry-l {
  display: flex;
  align-items: center;
  flex: 1;
  min-width: 0;
}
.wx-entry-ico {
  font-size: 30rpx;
  margin-right: 14rpx;
}
.wx-entry-txt {
  font-size: 24rpx;
  color: #fff;
  opacity: 0.9;
}
.wx-entry-btn {
  font-size: 22rpx;
  font-weight: 600;
  color: #0b7a50;
  background: #fff;
  border-radius: 999rpx;
  padding: 10rpx 26rpx;
  flex-shrink: 0;
}

/* 悬浮体重卡 */
.w-card {
  margin-top: 36rpx;
  background: #fff;
  border-radius: var(--r-lg);
  padding: 30rpx 32rpx;
  box-shadow: var(--shadow-card);
}
.w-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 26rpx;
}
.w-title {
  display: flex;
  align-items: center;
  .wt-label {
    font-size: 30rpx;
    font-weight: 600;
    color: var(--ink);
    margin-right: 16rpx;
  }
}
.pill {
  font-size: 20rpx;
  padding: 6rpx 18rpx;
  border-radius: 999rpx;
  &.green {
    color: var(--brand-deep);
    background: var(--brand-tint);
  }
  &.amber {
    color: #a86a10;
    background: var(--amber-tint);
  }
  &.danger {
    color: #b33a30;
    background: var(--red-tint);
  }
  &.blue {
    color: #2c6ea8;
    background: var(--blue-tint);
  }
}
.w-main {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
}
.w-num {
  display: flex;
  align-items: baseline;
  .num {
    font-size: 88rpx;
    font-weight: 700;
    color: var(--ink);
    line-height: 1;
  }
  .unit {
    font-size: 28rpx;
    color: var(--ink-3);
    margin-left: 8rpx;
  }
}
.w-side {
  text-align: right;
  padding-bottom: 4rpx;
  .side-label {
    font-size: 22rpx;
    color: var(--ink-3);
    display: block;
  }
  .side-val {
    display: flex;
    align-items: baseline;
    justify-content: flex-end;
    margin-top: 4rpx;
  }
  .side-num {
    font-size: 44rpx;
    font-weight: 600;
    color: var(--amber);
    &.good {
      color: var(--brand);
    }
  }
  .side-unit {
    font-size: 22rpx;
    color: var(--ink-3);
    margin-left: 6rpx;
  }
  .link-btn {
    display: inline-block;
    margin-top: 10rpx;
    font-size: 24rpx;
    color: #fff;
    background: var(--grad-brand);
    padding: 10rpx 26rpx;
    border-radius: 999rpx;
    box-shadow: var(--shadow-btn);
  }
}
.progress {
  margin-top: 10rpx;
  padding-top: 24rpx;
  border-top: 1rpx solid var(--line);
}
.bar {
  height: 14rpx;
  background: #e6efea;
  border-radius: 8rpx;
  overflow: hidden;
}
.fill {
  height: 100%;
  background: var(--grad-brand);
  border-radius: 8rpx;
  transition: width 0.4s;
}
.bar-ends {
  display: flex;
  justify-content: space-between;
  margin-top: 12rpx;
  font-size: 22rpx;
  color: var(--ink-3);
}

/* ============ 通用卡片 ============ */
.card {
  background: var(--card);
  border-radius: var(--r-lg);
  padding: 30rpx 32rpx;
  margin: 0 24rpx 24rpx;
  box-shadow: var(--shadow-card);
}
.card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 26rpx;
}
.head-l {
  display: flex;
  align-items: center;
}
.head-dot {
  width: 14rpx;
  height: 14rpx;
  border-radius: 50%;
  margin-right: 14rpx;
  &.c-green {
    background: var(--brand);
  }
  &.c-amber {
    background: var(--amber);
  }
  &.c-blue {
    background: var(--blue);
  }
}
.card-title {
  font-size: 32rpx;
  font-weight: 600;
  color: var(--ink);
}
.tag {
  font-size: 22rpx;
  padding: 8rpx 20rpx;
  border-radius: 999rpx;
  &.amber {
    color: #a86a10;
    background: var(--amber-tint);
  }
}

/* 今日热量 */
.ring-row {
  display: flex;
  align-items: center;
}
.ring {
  width: 216rpx;
  height: 216rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: inset 0 0 0 1rpx rgba(20, 94, 62, 0.04);
}
.ring-inner {
  width: 168rpx;
  height: 168rpx;
  border-radius: 50%;
  background: #fff;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  box-shadow: 0 6rpx 18rpx rgba(20, 94, 62, 0.08);
}
.ring-num {
  font-size: 46rpx;
  font-weight: 700;
  color: var(--ink);
}
.ring-label {
  font-size: 22rpx;
  color: var(--ink-3);
  margin-top: 4rpx;
}
.ring-info {
  margin-left: 36rpx;
  flex: 1;
}
.info-line {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 26rpx;
  color: var(--ink-2);
  margin-bottom: 20rpx;
  &:last-child {
    margin-bottom: 0;
  }
  .kpi {
    display: flex;
    align-items: center;
  }
}
.info-num {
  font-size: 30rpx;
  font-weight: 600;
  color: var(--ink);
}
.dot {
  width: 16rpx;
  height: 16rpx;
  border-radius: 50%;
  margin-right: 12rpx;
  &.in {
    background: var(--brand);
  }
  &.out {
    background: var(--blue);
  }
  &.budget {
    background: #cdd9d1;
  }
}
.macros {
  display: flex;
  margin-top: 28rpx;
  padding-top: 24rpx;
  border-top: 1rpx solid var(--line);
}
.macro {
  flex: 1;
  text-align: center;
  padding: 0 8rpx;
  .mv {
    display: block;
    font-size: 32rpx;
    font-weight: 600;
    color: var(--ink);
  }
  .ml {
    display: block;
    font-size: 22rpx;
    color: var(--ink-3);
    margin-top: 6rpx;
  }
}
.macro-bar {
  height: 6rpx;
  border-radius: 3rpx;
  margin: 0 auto 14rpx;
  max-width: 120rpx;
  transition: width 0.4s;
  &.p {
    background: var(--brand);
  }
  &.c {
    background: var(--amber);
  }
  &.f {
    background: var(--blue);
  }
}

/* 今日任务 */
.task-count {
  font-size: 22rpx;
  color: var(--ink-3);
}
.task {
  display: flex;
  align-items: center;
  padding: 20rpx 0;
  &:not(:last-child) {
    border-bottom: 1rpx solid var(--line);
  }
}
.task-box {
  width: 46rpx;
  height: 46rpx;
  border-radius: 50%;
  border: 2rpx solid #c9d8cf;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  background: #fff;
  &.done {
    background: var(--grad-brand);
    border-color: transparent;
  }
}
.tick {
  color: #fff;
  font-size: 26rpx;
  font-weight: 600;
}
.task-text {
  font-size: 28rpx;
  color: var(--ink-2);
  margin-left: 22rpx;
  flex: 1;
  &.done {
    color: var(--ink-3);
    text-decoration: line-through;
  }
}
.task-action {
  font-size: 24rpx;
  color: var(--brand-deep);
  background: var(--brand-tint);
  padding: 10rpx 26rpx;
  border-radius: 999rpx;
  font-weight: 500;
}

/* 本周打卡 */
.week-grid {
  display: flex;
  justify-content: space-between;
  padding: 4rpx 8rpx;
}
.week-day {
  display: flex;
  flex-direction: column;
  align-items: center;
}
.wd-label {
  font-size: 24rpx;
  color: var(--ink-3);
  margin-bottom: 12rpx;
  &.on {
    color: var(--brand-deep);
    font-weight: 600;
  }
}
.wd-badge {
  width: 52rpx;
  height: 52rpx;
  border-radius: 18rpx;
  background: #edf3ef;
  display: flex;
  align-items: center;
  justify-content: center;
  &.on {
    background: var(--grad-brand);
    box-shadow: 0 6rpx 14rpx rgba(14, 158, 104, 0.3);
  }
}
.wd-check {
  color: #fff;
  font-size: 26rpx;
  font-weight: 600;
}
.week-sum {
  margin-top: 28rpx;
  padding-top: 24rpx;
  border-top: 1rpx solid var(--line);
  font-size: 24rpx;
  color: var(--ink-2);
}
.hl {
  color: var(--brand-deep);
  font-weight: 600;
  padding: 0 4rpx;
}

/* 页脚 */
.page {
  padding-bottom: 48rpx;
  min-height: 100vh;
}
.disclaimer {
  margin: 8rpx 32rpx 0;
  font-size: 20rpx;
  color: var(--ink-4);
  text-align: center;
  line-height: 1.7;
}
</style>
