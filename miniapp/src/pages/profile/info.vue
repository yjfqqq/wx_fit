<template>
  <view class="page">
    <!-- ============ 基础资料 ============ -->
    <view class="card">
      <view class="card-head">
        <text class="card-title">基础资料</text>
        <text class="head-hint">会直接影响热量计算</text>
      </view>

      <view class="gender-grid" role="radiogroup" aria-label="性别">
        <view
          class="gcard"
          :class="{ on: form.gender === 1 }"
          role="radio"
          :aria-checked="form.gender === 1"
          @click="form.gender = 1"
        >
          <text class="g-ico">♂</text>
          <text class="g-txt">男生</text>
          <view class="check" v-if="form.gender === 1">✓</view>
        </view>
        <view
          class="gcard"
          :class="{ on: form.gender === 2 }"
          role="radio"
          :aria-checked="form.gender === 2"
          @click="form.gender = 2"
        >
          <text class="g-ico">♀</text>
          <text class="g-txt">女生</text>
          <view class="check" v-if="form.gender === 2">✓</view>
        </view>
      </view>

      <view class="g2">
        <view class="field">
          <text class="label">年龄</text>
          <view class="input-box">
            <input class="input" type="number" v-model="form.age" placeholder="请输入" placeholder-class="ph" />
            <text class="unit">岁</text>
          </view>
        </view>
        <view class="field">
          <text class="label">身高</text>
          <view class="input-box">
            <input class="input" type="digit" inputmode="decimal" v-model="form.height_cm" placeholder="请输入" placeholder-class="ph" />
            <text class="unit">cm</text>
          </view>
        </view>
      </view>
    </view>

    <!-- ============ 日常活动量 ============ -->
    <view class="card">
      <view class="card-head">
        <text class="card-title">日常活动量</text>
        <text class="head-hint">选择最接近日常的一项</text>
      </view>

      <view class="act-grid" role="radiogroup" aria-label="日常活动量">
        <view
          class="aopt"
          v-for="a in acts"
          :key="a.v"
          :class="{ on: form.activity_level === a.v, wide: a.v === 5 }"
          role="radio"
          :aria-checked="form.activity_level === a.v"
          @click="form.activity_level = a.v"
        >
          <view class="a-info">
            <text class="a-t">{{ a.t }}</text>
            <text class="a-s">{{ a.s }}</text>
          </view>
          <view class="radio" :class="{ on: form.activity_level === a.v }" />
        </view>
      </view>
    </view>

    <!-- ============ 底部固定保存栏 ============ -->
    <view class="save-bar">
      <view class="sb-l">
        <text class="sb-type">{{ summaryMain }}</text>
        <text class="sb-sub">{{ summarySub }}</text>
      </view>
      <button class="sb-btn" @click="save">保存资料</button>
    </view>
  </view>
</template>

<script setup>
import { computed, ref, onMounted } from "vue";
import { onShow } from "@dcloudio/uni-app";
import { authApi } from "@/api";
import { useUserStore } from "@/store/user";
import { applyTheme } from "@/utils/theme";

const user = useUserStore();

// 活动系数（与后端 calc.py ACTIVITY_FACTORS 一致）：1 久坐 2 轻度 3 中度 4 高度 5 极高
const acts = [
  { v: 1, t: "久坐少动", s: "日常几乎不运动" },
  { v: 2, t: "轻度活动", s: "每周运动 1-3 次" },
  { v: 3, t: "中度活动", s: "每周运动 3-5 次" },
  { v: 4, t: "高活动量", s: "每周运动 6-7 次" },
  { v: 5, t: "运动员级", s: "每天高强度训练" },
];

const form = ref({ gender: 0, age: "", height_cm: "", activity_level: 1 });

const actLabel = computed(
  () => acts.find((a) => a.v === form.value.activity_level)?.t || ""
);
const summaryMain = computed(() => {
  const f = form.value;
  const parts = [];
  parts.push(f.gender === 2 ? "女生" : f.gender === 1 ? "男生" : "未选性别");
  if (f.age) parts.push(f.age + "岁");
  if (f.height_cm) parts.push(f.height_cm + "cm");
  return parts.join(" · ");
});
const summarySub = computed(() =>
  actLabel.value ? `${actLabel.value} · 保存后热量预算同步更新` : "保存后热量预算同步更新"
);

function calcAge(birthday) {
  const b = new Date(birthday);
  const t = new Date();
  let age = t.getFullYear() - b.getFullYear();
  if (
    t.getMonth() + 1 < b.getMonth() + 1 ||
    (t.getMonth() + 1 === b.getMonth() + 1 && t.getDate() < b.getDate())
  )
    age--;
  return Math.max(age, 0);
}
function ageToBirthday(age) {
  const t = new Date();
  return `${t.getFullYear() - age}-${String(t.getMonth() + 1).padStart(2, "0")}-${String(t.getDate()).padStart(2, "0")}`;
}

async function save() {
  const f = form.value;
  if (!f.gender) {
    uni.showToast({ title: "请先选择性别", icon: "none" });
    return;
  }
  try {
    await user.ensureLogin();
    await authApi.updateProfile({
      gender: f.gender,
      birthday: f.age ? ageToBirthday(Number(f.age)) : null,
      height_cm: f.height_cm ? Number(f.height_cm) : null,
      activity_level: f.activity_level,
    });
    uni.showToast({ title: "已保存", icon: "success" });
    setTimeout(() => uni.navigateBack(), 600);
  } catch (e) {
    console.error(e);
  }
}

onMounted(async () => {
  try {
    await user.ensureLogin();
    await user.loadProfile();
    const p = user.profile;
    if (p) {
      form.value = {
        gender: p.gender || 0,
        age: p.birthday ? String(calcAge(p.birthday)) : "",
        height_cm: p.height_cm != null ? String(p.height_cm) : "",
        activity_level: p.activity_level || 1,
      };
    }
  } catch (e) {
    console.error(e);
  }
});

onShow(() => applyTheme());
</script>

<style scoped lang="scss">
.page {
  min-height: 100vh;
  box-sizing: border-box; /* padding 计入 100vh，内容一屏放得下时不出现滚动 */
  background: var(--bg);
  padding: var(--gap-card) 0 220rpx;
}

/* ============ 卡片 ============ */
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
.ph { color: var(--ink-3); }

/* ============ 基础资料 ============ */
.gender-grid {
  display: flex;
  gap: 16rpx;
  margin-bottom: 24rpx;
}
.gcard {
  flex: 1;
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8rpx;
  padding: 28rpx 0;
  border: 2rpx solid var(--line);
  border-radius: var(--r-md);
  background: var(--card);
  transition: all var(--d-fast) var(--e-out);
  .g-ico { font-size: 40rpx; color: var(--ink-3); line-height: 1; }
  .g-txt { font-size: 28rpx; font-weight: 600; color: var(--ink-2); }
  &.on {
    border-color: var(--brand);
    background: var(--brand-tint);
    .g-ico, .g-txt { color: var(--brand); }
  }
}
.check {
  position: absolute;
  top: 12rpx;
  right: 12rpx;
  width: 36rpx;
  height: 36rpx;
  border-radius: 50%;
  background: var(--brand);
  color: var(--on-brand);
  font-size: 22rpx;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}
.g2 {
  display: flex;
  gap: 16rpx;
}
.field {
  flex: 1;
  min-width: 0;
}
.label {
  display: block;
  margin-bottom: var(--gap-label);
  font-size: 25rpx;
  font-weight: 600;
  color: var(--ink-2);
}
/* 输入框：只保留一层浅色填充底，不描边 */
.input-box {
  display: flex;
  align-items: center;
  gap: 8rpx;
  height: 88rpx;
  padding: 0 24rpx;
  border: none;
  border-radius: var(--r-md);
  background: var(--surface-2);
  box-sizing: border-box;
}
.input {
  flex: 1;
  min-width: 0;
  height: 100%;
  border: none;
  font-size: 30rpx;
  font-weight: 600;
  color: var(--ink);
  text-align: right;
  background: transparent; /* mp-weixin 的 input 自带白底，必须显式透明 */
}
.unit {
  font-size: 24rpx;
  color: var(--ink-3);
  flex-shrink: 0;
}

/* ============ 日常活动量 ============ */
.act-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16rpx;
}
.aopt {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12rpx;
  padding: 20rpx 24rpx;
  min-height: 128rpx;
  border: 2rpx solid var(--line);
  border-radius: var(--r-md);
  background: var(--card);
  box-sizing: border-box;
  transition: all var(--d-fast) var(--e-out);
  &.wide { grid-column: span 2; }
  .a-info { min-width: 0; display: flex; flex-direction: column; gap: 4rpx; }
  .a-t { font-size: 26rpx; font-weight: 600; color: var(--ink-2); }
  .a-s { font-size: 20rpx; color: var(--ink-3); }
  .radio {
    width: 32rpx;
    height: 32rpx;
    border-radius: 50%;
    border: 2rpx solid var(--line-strong);
    flex-shrink: 0;
    box-sizing: border-box;
    transition: all var(--d-fast) var(--e-out);
  }
  &.on {
    border-color: var(--brand);
    background: var(--brand-tint);
    .a-t { color: var(--brand); }
    .radio { border-color: var(--brand); background: var(--brand); box-shadow: inset 0 0 0 6rpx var(--brand-tint); }
  }
}

/* ============ 底部固定保存栏 ============ */
.save-bar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24rpx;
  padding: 20rpx var(--pad-x);
  padding-bottom: calc(20rpx + env(safe-area-inset-bottom));
  background: var(--card);
  border-top: 1rpx solid var(--line);
}
.sb-l {
  display: flex;
  flex-direction: column;
  gap: 4rpx;
  min-width: 0;
}
.sb-type {
  font-size: 28rpx;
  font-weight: 700;
  color: var(--ink);
}
.sb-sub {
  font-size: 20rpx;
  color: var(--ink-3);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.sb-btn {
  flex-shrink: 0;
  margin: 0;
  padding: 0 48rpx;
  min-height: 88rpx;
  line-height: 88rpx;
  border-radius: var(--r-pill);
  background: var(--grad-brand);
  color: var(--on-brand);
  font-size: 30rpx;
  font-weight: 700;
  box-shadow: var(--shadow-btn);
  &::after { display: none; }
}
</style>
