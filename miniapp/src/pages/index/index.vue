<template>
  <view class="page">
    <!-- ============ 顶部问候（浅色头部，去掉全幅渐变） ============ -->
    <view class="hero">
      <view class="hero-inner">
        <text class="title">{{ greetTitle }}</text>
        <view class="greet-sub">
          <text class="slogan">本周已记录 {{ weekCount }} 天</text>
          <text class="date-chip">{{ dateText }}</text>
        </view>
      </view>
    </view>

    <!-- ============ 今日热量（首屏第一位：一天要查好几次） ============ -->
    <view class="card">
      <view class="card-head">
        <view class="head-l">
          <text class="head-dot c-amber" />
          <text class="card-title">今日热量</text>
        </view>
        <text class="tag amber" v-if="unknownCount">
          {{ unknownCount }} 条未计热量
        </text>
      </view>

      <view class="ring-row">
        <view
          class="ring"
          :style="ringStyle"
          role="img"
          :aria-label="'今日热量进度环：还可摄入 ' + remainingText + '，已摄入 ' + intake + ' 千卡，消耗 ' + burn + ' 千卡'"
        >
          <view class="ring-inner">
            <text class="ring-num">{{ remainingText }}</text>
            <text class="ring-label">还可摄入</text>
          </view>
        </view>

        <view class="ring-info">
          <view class="info-line">
            <view class="kpi"><view class="dot in" /><text>摄入</text></view>
            <text class="info-num">{{ intake }} kcal</text>
          </view>
          <view class="info-line">
            <view class="kpi"><view class="dot out" /><text>消耗</text></view>
            <text class="info-num">{{ burn }} kcal</text>
          </view>
          <view class="info-line">
            <view class="kpi"><view class="dot budget" /><text>预算</text></view>
            <text class="info-num">{{ budgetText }}</text>
          </view>
        </view>
      </view>

      <!-- 供能比：按蛋白×4 / 碳水×4 / 脂肪×9 计算，替代三条各自为政的进度条 -->
      <view
        class="mbar"
        v-if="macroPct"
        role="img"
        :aria-label="'供能比：蛋白 ' + protein + ' 克、碳水 ' + carbs + ' 克、脂肪 ' + fat + ' 克'"
      >
        <view class="mseg p" :style="{ width: macroPct.p + '%' }" />
        <view class="mseg c" :style="{ width: macroPct.c + '%' }" />
        <view class="mseg f" :style="{ width: macroPct.f + '%' }" />
      </view>
      <view class="mlegend" v-if="macroPct">
        <view class="ml-item"><view class="ml-dot p" /><text>蛋白</text><text class="mv num">{{ protein }}g</text></view>
        <view class="ml-item"><view class="ml-dot c" /><text>碳水</text><text class="mv num">{{ carbs }}g</text></view>
        <view class="ml-item"><view class="ml-dot f" /><text>脂肪</text><text class="mv num">{{ fat }}g</text></view>
      </view>
    </view>

    <!-- ============ 体重（第二位，横向压缩：200rpx 级 → 290rpx 级） ============ -->
    <view class="card">
      <view class="card-head">
        <view class="head-l">
          <text class="head-dot c-green" />
          <text class="card-title">体重</text>
        </view>
        <text class="pill g" v-if="bmi">BMI {{ bmi }} · {{ bmiLevel }}</text>
      </view>

      <view class="w-line">
        <view class="w-big">
          <text class="big num">{{ currentWeight ?? "--" }}</text>
          <text class="big-unit">kg</text>
        </view>
        <text
          class="w-gap num"
          :class="{ good: gap != null && gap <= 0 }"
          v-if="targetWeight && gap != null"
        >{{ gap > 0 ? "距目标 " + gap.toFixed(1) + " kg" : "已达成" }}</text>
      </view>

      <view class="progress" v-if="progress !== null">
        <view class="bar"><view class="fill" :style="{ width: progress * 100 + '%' }" /></view>
        <view class="bar-ends">
          <text>{{ startWeight ?? "?" }} kg 起</text>
          <text>目标 {{ targetWeight }} kg</text>
        </view>
      </view>
      <view class="nogoal" v-else-if="!targetWeight">
        <text class="nogoal-txt">还没设目标</text>
        <navigator url="/pages/profile/goal" class="link-btn hit">去设置</navigator>
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
        <view class="task-action hit" v-if="!t.done" @click="goRecord(t.tab)">去记录</view>
      </view>
    </view>

    <!-- ============ 本周打卡（7 等分，不再 space-between） ============ -->
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
        <text class="hl num">{{ weekCount }}</text>
        天,体重变化
        <text class="hl num">{{ weekChangeText }}</text>
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
import { applyTheme } from "@/utils/theme";

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
  if (l.includes("肥胖")) return "r";
  if (l.includes("偏胖") || l.includes("超重")) return "a";
  if (l.includes("偏瘦")) return "b";
  return "g";
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
    ? (Math.min(intake.value / budget.value, 1.5) / 1.5) * 100
    : 0;
  const over = budget.value && intake.value > budget.value;
  const color = over ? "var(--red-fill)" : "var(--brand)";
  return {
    background: `conic-gradient(${color} ${pct}%, var(--surface-2) ${pct}%)`,
  };
});

// 供能比：热量来源占比（蛋白/碳水 4 kcal/g，脂肪 9 kcal/g）
const macroPct = computed(() => {
  const p = protein.value * 4;
  const c = carbs.value * 4;
  const f = fat.value * 9;
  const t = p + c + f;
  if (!t) return null;
  const r = (v) => Math.round((v / t) * 1000) / 10;
  return { p: r(p), c: r(c), f: r(f) };
});

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

async function load() {
  try {
    await user.ensureLogin();
    // 刷新用户资料，保证头像昵称修改后即时生效
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

  } catch (e) {
    console.error(e);
  }
}

onShow(() => {
  load();
  applyTheme();
});
</script>

<style scoped lang="scss">
/* ============ 页面 ============ */
.page {
  background: var(--bg);
  padding-bottom: 48rpx;
  min-height: 100vh;
}

/* ============ 顶部问候（浅色，不再用全幅渐变） ============ */
.hero {
  padding: 32rpx var(--pad-x) 8rpx;
}
.hero-inner {
  .title {
    display: block;
    font-size: 50rpx;
    font-weight: 700;
    color: var(--ink);
    letter-spacing: -1rpx;
    line-height: 1.2;
  }
  .greet-sub {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-top: 12rpx;
  }
  .slogan {
    font-size: 25rpx;
    color: var(--brand);
    font-weight: 600;
    flex: 1;
    min-width: 0;
  }
  .date-chip {
    font-size: 23rpx;
    color: var(--ink-3);
    background: var(--card);
    border: 1rpx solid var(--line);
    padding: 8rpx 24rpx;
    border-radius: var(--r-pill);
    margin-left: 20rpx;
    flex-shrink: 0;
    font-variant-numeric: tabular-nums;
  }
}

/* ============ 通用卡片 ============ */
.card {
  background: var(--card);
  border: 1rpx solid var(--line);
  border-radius: var(--r-lg);
  padding: var(--pad-card);
  margin: 0 var(--pad-x) var(--gap-card);
  box-shadow: var(--shadow-card);
  overflow: hidden;
}
.card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24rpx;
}
.head-l {
  display: flex;
  align-items: center;
  min-width: 0;
}
.head-dot {
  width: 12rpx;
  height: 12rpx;
  border-radius: 50%;
  margin-right: 16rpx;
  flex-shrink: 0;
  &.c-green { background: var(--brand); }
  &.c-amber { background: var(--amber-fill); }
  &.c-blue  { background: var(--blue-fill); }
}
.card-title {
  font-size: 32rpx;
  font-weight: 600;
  color: var(--ink);
  letter-spacing: -0.4rpx;
}
.tag {
  font-size: 22rpx;
  padding: 8rpx 20rpx;
  border-radius: var(--r-pill);
  flex-shrink: 0;
  &.amber { color: var(--amber); background: var(--amber-tint); }
}
.pill {
  font-size: 21rpx;
  font-weight: 700;
  padding: 6rpx 16rpx;
  border-radius: var(--r-pill);
  flex-shrink: 0;
  &.g { color: var(--brand); background: var(--brand-tint); }
  &.a { color: var(--amber);  background: var(--amber-tint); }
  &.r { color: var(--red);    background: var(--red-tint); }
  &.b { color: var(--blue);   background: var(--blue-tint); }
}
.num { font-variant-numeric: tabular-nums; }

/* ============ 今日热量 ============ */
.ring-row {
  display: flex;
  align-items: center;
}
.ring {
  width: 200rpx;
  height: 200rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.ring-inner {
  width: 156rpx;
  height: 156rpx;
  border-radius: 50%;
  background: var(--card);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
.ring-num {
  font-size: 44rpx;
  font-weight: 700;
  color: var(--ink);
  letter-spacing: -1rpx;
  font-variant-numeric: tabular-nums;
}
.ring-label {
  font-size: 21rpx;
  color: var(--ink-3);
  margin-top: 4rpx;
}
.ring-info {
  margin-left: 32rpx;
  flex: 1;
  min-width: 0;
}
.info-line {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 26rpx;
  color: var(--ink-2);
  margin-bottom: 20rpx;
  &:last-child { margin-bottom: 0; }
  .kpi { display: flex; align-items: center; }
}
.info-num {
  font-size: 30rpx;
  font-weight: 600;
  color: var(--ink);
  font-variant-numeric: tabular-nums;
}
.dot {
  width: 14rpx;
  height: 14rpx;
  border-radius: 50%;
  margin-right: 12rpx;
  flex-shrink: 0;
  &.in { background: var(--brand); }
  &.out { background: var(--blue-fill); }
  &.budget { background: var(--line-strong); }
}

/* 供能比分段条 */
.mbar {
  display: flex;
  height: 16rpx;
  border-radius: var(--r-pill);
  overflow: hidden;
  background: var(--surface-2);
  margin-top: 32rpx;
}
.mseg {
  height: 100%;
  &.p { background: var(--brand); }
  &.c { background: var(--amber-fill); }
  &.f { background: var(--blue-fill); }
}
.mlegend {
  display: flex;
  justify-content: space-between;
  margin-top: 16rpx;
  gap: 12rpx;
}
.ml-item {
  display: flex;
  align-items: center;
  gap: 8rpx;
  font-size: 23rpx;
  color: var(--ink-3);
  min-width: 0;
}
.ml-dot {
  width: 14rpx;
  height: 14rpx;
  border-radius: 4rpx;
  flex-shrink: 0;
  &.p { background: var(--brand); }
  &.c { background: var(--amber-fill); }
  &.f { background: var(--blue-fill); }
}
.mv {
  color: var(--ink);
  font-weight: 600;
}

/* ============ 体重卡（横向压缩） ============ */
.w-line {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 20rpx;
}
.w-big {
  display: flex;
  align-items: baseline;
  gap: 6rpx;
  min-width: 0;
  .big {
    font-size: 64rpx;
    font-weight: 700;
    color: var(--ink);
    letter-spacing: -2rpx;
    line-height: 1.1;
  }
  .big-unit {
    font-size: 26rpx;
    font-weight: 600;
    color: var(--ink-3);
  }
}
.w-gap {
  font-size: 26rpx;
  font-weight: 600;
  color: var(--amber);
  flex-shrink: 0;
  &.good { color: var(--brand); }
}
.progress {
  margin-top: 24rpx;
  padding-top: 24rpx;
  border-top: 1rpx solid var(--line);
}
.bar {
  height: 16rpx;
  background: var(--surface-2);
  border-radius: var(--r-pill);
  overflow: hidden;
}
.fill {
  height: 100%;
  background: var(--grad-brand);
  border-radius: var(--r-pill);
  transition: width var(--d-slow) var(--e-out);
}
.bar-ends {
  display: flex;
  justify-content: space-between;
  margin-top: 12rpx;
  font-size: 22rpx;
  color: var(--ink-3);
  font-variant-numeric: tabular-nums;
}
.nogoal {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 24rpx;
  padding-top: 24rpx;
  border-top: 1rpx solid var(--line);
  .nogoal-txt { font-size: 25rpx; color: var(--ink-3); }
  .link-btn {
    font-size: 25rpx;
    font-weight: 600;
    color: var(--on-brand);
    background: var(--grad-brand);
    padding: 16rpx 32rpx;
    border-radius: var(--r-pill);
    box-shadow: var(--shadow-btn);
  }
}

/* ============ 今日任务 ============ */
.task-count {
  font-size: 22rpx;
  color: var(--ink-3);
  flex-shrink: 0;
}
.task {
  display: flex;
  align-items: center;
  padding: 16rpx 0;
  &:not(:last-child) { border-bottom: 1rpx solid var(--line); }
}
.task-box {
  width: 46rpx;
  height: 46rpx;
  border-radius: 50%;
  border: 2rpx solid var(--line-strong);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  background: var(--card);
  &.done { background: var(--grad-brand); border-color: transparent; }
}
.tick { color: var(--on-brand); font-size: 26rpx; font-weight: 600; }
.task-text {
  font-size: 28rpx;
  color: var(--ink-2);
  margin-left: 20rpx;
  flex: 1;
  min-width: 0;
  &.done { color: var(--ink-3); text-decoration: line-through; }
}
.task-action {
  font-size: 24rpx;
  font-weight: 600;
  color: var(--brand);
  background: var(--brand-tint);
  padding: 12rpx 24rpx;
  border-radius: var(--r-pill);
  flex-shrink: 0;
}

/* ============ 本周打卡（7 等分） ============ */
.week-grid {
  display: flex;
  gap: 8rpx;
}
.week-day {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.wd-label {
  font-size: 23rpx;
  color: var(--ink-3);
  margin-bottom: 12rpx;
  &.on { color: var(--brand); font-weight: 700; }
}
.wd-badge {
  width: 56rpx;
  height: 56rpx;
  max-width: 100%;
  border-radius: 20rpx;
  background: var(--surface-2);
  display: flex;
  align-items: center;
  justify-content: center;
  &.on {
    background: var(--grad-brand);
    box-shadow: 0 6rpx 14rpx rgba(6, 121, 76, 0.28);
  }
}
.wd-check { color: var(--on-brand); font-size: 26rpx; font-weight: 600; }
.week-sum {
  margin-top: 32rpx;
  padding-top: 24rpx;
  border-top: 1rpx solid var(--line);
  font-size: 24rpx;
  color: var(--ink-2);
  line-height: 1.7;
}
.hl {
  color: var(--brand);
  font-weight: 700;
  padding: 0 4rpx;
}

/* ============ 页脚 ============ */
.disclaimer {
  margin: 8rpx var(--pad-x) 0;
  font-size: 20rpx;
  color: var(--ink-3);
  text-align: center;
  line-height: 1.7;
}
</style>
