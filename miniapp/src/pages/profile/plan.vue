<template>
  <view class="page">
    <!-- ============ 每日预算（结论） ============ -->
    <view class="card hero-card">
      <view class="card-head">
        <text class="card-title">每日热量预算</text>
        <text class="head-hint" v-if="plan && plan.has_goal">按当前目标测算</text>
      </view>

      <view class="big-row" v-if="plan && plan.daily_budget != null">
        <text class="big num">{{ Math.round(plan.daily_budget) }}</text>
        <text class="big-unit">kcal / 天</text>
      </view>
      <view class="empty" v-else>
        <view class="empty-ico">🔥</view>
        <text class="empty-text">还无法测算</text>
        <text class="empty-sub">补全性别、年龄、身高和活动量后自动生成</text>
        <button class="link-btn" @click="goInfo">去完善资料</button>
      </view>
    </view>

    <!-- ============ 测算拆解 ============ -->
    <view class="card" v-if="plan">
      <view class="card-head">
        <text class="card-title">测算过程</text>
        <text class="head-hint">Mifflin-St Jeor 公式</text>
      </view>

      <view class="step">
        <view class="step-l">
          <text class="step-t">基础代谢 BMR</text>
          <text class="step-s">{{ bmrNote }}</text>
        </view>
        <text class="step-v num">{{ num(plan.bmr) }}</text>
      </view>

      <view class="step">
        <view class="step-l">
          <text class="step-t">活动系数</text>
          <text class="step-s">{{ actNote }}</text>
        </view>
        <text class="step-v num">× {{ factorText }}</text>
      </view>

      <view class="step sum">
        <view class="step-l">
          <text class="step-t">日常消耗 TDEE</text>
          <text class="step-s">BMR × 活动系数</text>
        </view>
        <text class="step-v num">{{ num(plan.tdee) }}</text>
      </view>

      <view class="step">
        <view class="step-l">
          <text class="step-t">每日缺口</text>
          <text class="step-s">{{ deficitNote }}</text>
        </view>
        <text class="step-v num minus">{{ deficitText }}</text>
      </view>

      <view class="step total">
        <view class="step-l">
          <text class="step-t">建议摄入</text>
          <text class="step-s">不低于基础代谢与安全下限</text>
        </view>
        <text class="step-v num">{{ num(plan.daily_budget) }}</text>
      </view>
    </view>

    <!-- ============ BMI ============ -->
    <view class="card" v-if="plan && plan.bmi != null">
      <view class="card-head">
        <text class="card-title">身体质量指数 BMI</text>
        <text class="pill" :class="bmiClass">{{ plan.bmi_level }}</text>
      </view>
      <view class="bmi-row">
        <text class="bmi-num num">{{ plan.bmi }}</text>
        <view class="bmi-scale">
          <view class="scale-bar" />
          <view class="scale-marks">
            <text>偏瘦</text><text>正常</text><text>超重</text><text>肥胖</text>
          </view>
        </view>
      </view>
    </view>

    <!-- ============ 目标进展 ============ -->
    <view class="card" v-if="plan && plan.has_goal">
      <view class="card-head">
        <text class="card-title">目标进展</text>
        <text class="head-hint">来自最近记录</text>
      </view>
      <view class="kv">
        <text class="k">当前体重</text>
        <text class="v num">{{ plan.current_weight != null ? plan.current_weight + " kg" : "--" }}</text>
      </view>
      <view class="kv">
        <text class="k">周均变化</text>
        <text class="v num">{{ weeklyText }}</text>
      </view>
      <view class="kv">
        <text class="k">预计达成</text>
        <text class="v num">{{ plan.predict_date || "数据不足" }}</text>
      </view>
      <view class="progress" v-if="plan.progress != null">
        <view class="bar"><view class="fill" :style="{ width: Math.min(plan.progress, 1) * 100 + '%' }" /></view>
        <view class="bar-ends">
          <text>目标完成度</text>
          <text class="num">{{ Math.round(plan.progress * 100) }}%</text>
        </view>
      </view>
    </view>

    <view class="actions" v-if="plan">
      <button class="act-btn ghost" @click="goInfo">修改个人资料</button>
      <button class="act-btn" @click="goGoal">调整减重目标</button>
    </view>

    <view class="disclaimer">数据仅供个人参考，不构成医疗建议</view>
  </view>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { onShow } from "@dcloudio/uni-app";
import { authApi, statsApi } from "@/api";
import { useUserStore } from "@/store/user";
import { applyTheme } from "@/utils/theme";

const user = useUserStore();
const plan = ref(null);
const profile = ref(null);
const goal = ref(null);

// 活动系数（与后端 calc.py ACTIVITY_FACTORS 一致）
const FACTORS = { 1: 1.2, 2: 1.375, 3: 1.55, 4: 1.725, 5: 1.9 };
const ACTS = {
  1: "久坐少动 · 日常几乎不运动",
  2: "轻度活动 · 每周运动 1-3 次",
  3: "中度活动 · 每周运动 3-5 次",
  4: "高活动量 · 每周运动 6-7 次",
  5: "运动员级 · 每天高强度训练",
};

function num(v) {
  return v == null ? "--" : Math.round(v);
}

const factorText = computed(() => FACTORS[profile.value?.activity_level || 1] ?? 1.2);
const actNote = computed(() => ACTS[profile.value?.activity_level || 1] || "未设置活动量");

const bmrNote = computed(() => {
  const p = profile.value;
  if (!p) return "补全资料后计算";
  const g = p.gender === 2 ? "女" : p.gender === 1 ? "男" : "未选性别";
  let age = "";
  if (p.birthday) {
    const b = new Date(p.birthday);
    const t = new Date();
    let a = t.getFullYear() - b.getFullYear();
    if (t.getMonth() + 1 < b.getMonth() + 1 || (t.getMonth() + 1 === b.getMonth() + 1 && t.getDate() < b.getDate())) a--;
    age = Math.max(a, 0) + "岁";
  }
  const h = p.height_cm ? p.height_cm + "cm" : "身高未填";
  return `${g}${age ? " · " + age : ""} · ${h}`;
});

const deficitText = computed(() => {
  if (!goal.value) return "--";
  const d = Number(goal.value.daily_deficit) || 0;
  return d > 0 ? `- ${d}` : "0";
});
const deficitNote = computed(() => {
  if (!goal.value) return "未设置目标";
  const d = Number(goal.value.daily_deficit) || 0;
  return d > 0 ? "按当前减重目标设定" : "当前为维持体重的节奏";
});
const weeklyText = computed(() => {
  const r = plan.value?.weekly_rate;
  if (r == null) return "数据不足";
  const v = Number(r);
  if (Math.abs(v) < 0.1) return "基本持平";
  return (v > 0 ? "+" : "") + v.toFixed(2) + " kg/周";
});
const bmiClass = computed(() => {
  const l = plan.value?.bmi_level || "";
  if (l.includes("肥胖")) return "r";
  if (l.includes("超重") || l.includes("偏胖")) return "a";
  if (l.includes("偏瘦")) return "b";
  return "g";
});

function goInfo() {
  uni.navigateTo({ url: "/pages/profile/info" });
}
function goGoal() {
  uni.navigateTo({ url: "/pages/profile/goal" });
}

onMounted(async () => {
  try {
    await user.ensureLogin();
    await user.loadProfile();
    profile.value = user.profile;
    const [pl, g] = await Promise.all([statsApi.plan(), authApi.getGoal().catch(() => null)]);
    plan.value = pl;
    goal.value = g;
  } catch (e) {
    console.error(e);
  }
});

onShow(() => applyTheme());
</script>

<style scoped lang="scss">
.page {
  min-height: 100vh;
  box-sizing: border-box;
  background: var(--bg);
  padding: var(--gap-card) 0 64rpx;
}
.card {
  background: var(--card);
  border: 1rpx solid var(--line);
  border-radius: var(--r-lg);
  padding: var(--pad-card);
  margin: 0 var(--pad-x) var(--gap-card);
  box-shadow: var(--shadow-card);
}
.card-head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 24rpx;
}
.card-title {
  font-size: 32rpx;
  font-weight: 600;
  color: var(--ink);
  letter-spacing: -0.4rpx;
}
.head-hint {
  font-size: 21rpx;
  color: var(--ink-3);
  flex-shrink: 0;
}
.num { font-variant-numeric: tabular-nums; }

/* 预算大数字 */
.big-row {
  display: flex;
  align-items: baseline;
  gap: 12rpx;
}
.big {
  font-size: 88rpx;
  font-weight: 700;
  color: var(--brand);
  letter-spacing: -3rpx;
  line-height: 1.1;
}
.big-unit {
  font-size: 26rpx;
  font-weight: 600;
  color: var(--ink-3);
}
.empty {
  text-align: center;
  padding: 24rpx 0 8rpx;
  .empty-ico { font-size: 64rpx; margin-bottom: 16rpx; }
  .empty-text { display: block; font-size: 28rpx; font-weight: 600; color: var(--ink-2); }
  .empty-sub { display: block; font-size: 22rpx; color: var(--ink-3); margin-top: 8rpx; }
}
.link-btn {
  margin-top: 24rpx;
  padding: 0 48rpx;
  height: 80rpx;
  line-height: 80rpx;
  border-radius: var(--r-pill);
  background: var(--grad-brand);
  color: var(--on-brand);
  font-size: 28rpx;
  font-weight: 700;
  box-shadow: var(--shadow-btn);
  &::after { display: none; }
}

/* 测算过程 */
.step {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20rpx;
  padding: 20rpx 0;
  border-bottom: 1rpx solid var(--line);
  &:last-child { border-bottom: none; }
  .step-l { min-width: 0; display: flex; flex-direction: column; gap: 4rpx; }
  .step-t { font-size: 26rpx; font-weight: 600; color: var(--ink); }
  .step-s { font-size: 20rpx; color: var(--ink-3); }
  .step-v { font-size: 30rpx; font-weight: 700; color: var(--ink); flex-shrink: 0; }
  &.sum .step-v { color: var(--ink-2); }
  .step-v.minus { color: var(--amber); }
  &.total {
    .step-v { color: var(--brand); font-size: 34rpx; }
  }
}

/* BMI */
.pill {
  font-size: 21rpx;
  font-weight: 700;
  padding: 6rpx 16rpx;
  border-radius: var(--r-pill);
  flex-shrink: 0;
  &.g { color: var(--brand); background: var(--brand-tint); }
  &.a { color: var(--amber); background: var(--amber-tint); }
  &.r { color: var(--red); background: var(--red-tint); }
  &.b { color: var(--blue); background: var(--blue-tint); }
}
.bmi-row {
  display: flex;
  align-items: center;
  gap: 24rpx;
}
.bmi-num {
  font-size: 56rpx;
  font-weight: 700;
  color: var(--ink);
  letter-spacing: -2rpx;
  line-height: 1.1;
}
.bmi-scale {
  flex: 1;
  min-width: 0;
}
.scale-bar {
  height: 12rpx;
  border-radius: var(--r-pill);
  background: linear-gradient(90deg, var(--blue-fill) 0 25%, var(--brand) 25% 50%, var(--amber-fill) 50% 75%, var(--red-fill) 75% 100%);
}
.scale-marks {
  display: flex;
  justify-content: space-between;
  margin-top: 12rpx;
  font-size: 19rpx;
  color: var(--ink-3);
}

/* 目标进展 */
.kv {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16rpx 0;
  border-bottom: 1rpx solid var(--line);
  .k { font-size: 26rpx; color: var(--ink-2); }
  .v { font-size: 28rpx; font-weight: 600; color: var(--ink); }
}
.progress {
  margin-top: 24rpx;
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
}
.bar-ends {
  display: flex;
  justify-content: space-between;
  margin-top: 12rpx;
  font-size: 22rpx;
  color: var(--ink-3);
}

/* 底部操作 */
.actions {
  display: flex;
  gap: 16rpx;
  margin: 0 var(--pad-x);
}
.act-btn {
  flex: 1;
  margin: 0;
  height: 88rpx;
  line-height: 88rpx;
  border-radius: var(--r-pill);
  background: var(--grad-brand);
  color: var(--on-brand);
  font-size: 29rpx;
  font-weight: 700;
  box-shadow: var(--shadow-btn);
  &::after { display: none; }
  &.ghost {
    background: var(--surface-2);
    color: var(--ink-2);
    box-shadow: none;
    border: 1rpx solid var(--line);
  }
}
.disclaimer {
  margin: 24rpx var(--pad-x) 0;
  font-size: 20rpx;
  color: var(--ink-3);
  text-align: center;
}
</style>
