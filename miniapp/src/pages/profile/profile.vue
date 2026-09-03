<template>
  <view class="page">
    <!-- ============ 顶部个人主页 ============ -->
    <view class="profile-hero" @click="goWxAuth">
      <image
        v-if="user.avatarSrc && !avatarBroken"
        class="hero-avatar"
        :src="user.avatarSrc"
        mode="aspectFill"
        @error="onAvatarError"
      />
      <view v-else class="hero-avatar hero-avatar-ph" :class="genderClass">
        <text class="hero-avatar-char">{{ user.displayName.slice(0, 1) }}</text>
      </view>
      <view class="hero-name-row">
        <text class="hero-name">{{ user.displayName }}</text>
      </view>
      <text class="hero-stat">累计记录 {{ overview ? overview.recorded_days : 0 }} 天</text>
    </view>

    <!-- ============ 个人资料入口 ============ -->
    <view class="card menu-card" @click="showProfileForm = !showProfileForm">
      <view class="menu">
        <view class="menu-left">
          <view class="menu-ico profile">📝</view>
          <view class="menu-txt">
            <text class="menu-title">个人资料</text>
            <text class="menu-sub">性别、生日、身高、活动量</text>
          </view>
        </view>
        <text class="menu-arrow" :class="{ open: showProfileForm }">›</text>
      </view>
    </view>

    <!-- ============ 我的资料 ============ -->
    <view class="card" v-if="showProfileForm">
      <view class="card-head">
        <view class="head-l">
          <text class="head-dot c-green" />
          <text class="card-title">我的资料</text>
        </view>
      </view>

      <view class="field">
        <text class="label">性别</text>
        <view class="seg">
          <view
            class="seg-item"
            :class="{ on: form.gender === g.value }"
            v-for="g in genders"
            :key="g.value"
            @click="form.gender = g.value"
            >{{ g.label }}</view
          >
        </view>
      </view>

      <view class="field">
        <text class="label">出生日期</text>
        <picker mode="date" :value="form.birthday" :end="todayStr" @change="onBirthday">
          <view class="picker" :class="{ empty: !form.birthday }">
            {{ form.birthday || "请选择" }}
            <text class="chev-r">›</text>
          </view>
        </picker>
      </view>

      <view class="field-row">
        <view class="field flex1">
          <text class="label">身高（cm）</text>
          <view class="input-wrap">
            <input class="input" type="digit" v-model="form.height_cm" placeholder="170" />
            <text class="unit-suffix" v-if="form.height_cm">cm</text>
          </view>
        </view>
        <view class="field flex1">
          <text class="label">日常活动量</text>
          <picker
            :range="activityLabels"
            :value="form.activity_level - 1"
            @change="onActivity"
          >
            <view class="picker">{{ activityLabels[form.activity_level - 1] }}</view>
          </picker>
        </view>
      </view>

      <button class="btn" @click="save">保存资料</button>
    </view>

    <!-- ============ 目标 ============ -->
    <view class="card">
      <view class="card-head">
        <view class="head-l">
          <text class="head-dot c-amber" />
          <text class="card-title">减重目标</text>
        </view>
        <view class="link-chip" @click="goGoal">{{ hasGoal ? "修改" : "去设置" }}</view>
      </view>

      <view class="goal-row" v-if="hasGoal">
        <view class="goal-item">
          <view class="goal-circle start">
            <text class="gv">{{ goal.start_weight }}</text>
          </view>
          <text class="gl">起始 kg</text>
        </view>
        <view class="goal-flow">
          <text class="flow-arrow">→</text>
          <text class="flow-tag">{{ goal.daily_deficit }}<text class="ft-unit"> 千卡/日</text></text>
        </view>
        <view class="goal-item">
          <view class="goal-circle target">
            <text class="gv">{{ goal.target_weight }}</text>
          </view>
          <text class="gl">目标 kg</text>
        </view>
      </view>
      <view class="empty-goal" v-else>
        <text class="eg-main">还没有减重目标</text>
        <text class="eg-sub">设置后这里会显示进度与每日热量预算</text>
        <view class="eg-btn" @click="goGoal">立即设置</view>
      </view>
    </view>

    <!-- ============ 热量测算 ============ -->
    <view class="card" v-if="plan && plan.bmr">
      <view class="card-head">
        <view class="head-l">
          <text class="head-dot c-blue" />
          <text class="card-title">我的热量测算</text>
        </view>
      </view>
      <view class="plan-grid">
        <view class="plan-item">
          <text class="pv">{{ Math.round(plan.bmr) }}</text>
          <text class="pl">基础代谢 BMR</text>
        </view>
        <view class="plan-sep" />
        <view class="plan-item">
          <text class="pv">{{ Math.round(plan.tdee) }}</text>
          <text class="pl">每日总消耗 TDEE</text>
        </view>
        <view class="plan-sep" />
        <view class="plan-item hl">
          <text class="pv">{{ plan.daily_budget }}</text>
          <text class="pl">建议摄入</text>
        </view>
      </view>
      <view class="plan-note">
        <text class="note-ico">💡</text>
        <text>建议摄入 = TDEE − 每日缺口,且不会低于基础代谢</text>
      </view>
    </view>

    <!-- ============ 记录概览 ============ -->
    <view class="card" v-if="overview">
      <view class="card-head">
        <view class="head-l">
          <text class="head-dot c-green" />
          <text class="card-title">记录概览</text>
        </view>
      </view>
      <view class="stat-grid">
        <view class="stat">
          <text class="sv hl">{{ lostText }}</text>
          <text class="sl">累计减重 kg</text>
        </view>
        <view class="stat">
          <text class="sv">{{ overview.streak_days }}</text>
          <text class="sl">连续记录天</text>
        </view>
        <view class="stat">
          <text class="sv">{{ overview.recorded_days }}</text>
          <text class="sl">累计记录天</text>
        </view>
      </view>
    </view>

    <!-- ============ 其他 ============ -->
    <view class="card">
      <view class="card-head">
        <view class="head-l">
          <text class="head-dot c-amber" />
          <text class="card-title">其他</text>
        </view>
      </view>
      <view class="menu" @click="onRemind">
        <view class="menu-left">
          <view class="menu-ico bell">🔔</view>
          <view class="menu-txt">
            <text class="menu-title">每日体重打卡提醒</text>
            <text class="menu-sub" :class="{ on: remind.enabled }">{{ remindText }}</text>
          </view>
        </view>
        <view class="menu-right">
          <view class="switch" :class="{ on: remind.enabled }">
            <view class="knob" />
          </view>
        </view>
      </view>
      <view class="menu" @click="goCustom">
        <view class="menu-left">
          <view class="menu-ico food">🍱</view>
          <view class="menu-txt">
            <text class="menu-title">管理自定义食物</text>
          </view>
        </view>
        <text class="menu-arrow">›</text>
      </view>
      <view class="menu" @click="exportCsv">
        <view class="menu-left">
          <view class="menu-ico data">📊</view>
          <view class="menu-txt">
            <text class="menu-title">导出我的数据（CSV）</text>
          </view>
        </view>
        <text class="menu-arrow">›</text>
      </view>
      <text class="card-hint" v-if="remind.enabled">
        订阅消息为一次性授权,收到提醒后回小程序再开启一次即可续订
      </text>
    </view>

    <view class="logout" @click="logout">退出登录</view>
    <view class="disclaimer">本工具仅用于个人数据记录,不构成医疗建议</view>
  </view>
</template>

<script setup>
import { ref, computed } from "vue";
import { onShow } from "@dcloudio/uni-app";
import { authApi, statsApi, subscribeApi } from "@/api";
import { BASE_URL } from "@/api/request";
import { useUserStore } from "@/store/user";
import { today } from "@/utils/date";

const user = useUserStore();
const todayStr = today(); // 本地时区的今天（toISOString 是 UTC，凌晨会差一天）

const genders = [
  { value: 1, label: "男" },
  { value: 2, label: "女" },
];
const activityLabels = ["久坐", "轻度活动", "中度活动", "高强度", "运动员级"];

const form = ref({ gender: 1, birthday: "", height_cm: "", activity_level: 1 });
const goal = ref(null);
const plan = ref(null);
const overview = ref(null);
const showProfileForm = ref(false);
const remind = ref({ enabled: false, remind_time: "21:00", template_id: "" });
// 头像加载失败时置 true，退回首字占位图，避免留一片空白
const avatarBroken = ref(false);

const hasGoal = computed(() => !!(goal.value && goal.value.target_weight));
const genderClass = computed(() => (form.value.gender === 2 ? "girl" : "boy"));
const remindText = computed(() =>
  remind.value.enabled
    ? `已开启 · 每天 ${remind.value.remind_time}`
    : "未开启"
);
const lostText = computed(() => {
  const v = overview.value?.total_lost;
  return v == null ? "--" : Number(v).toFixed(1);
});

function goWxAuth() {
  uni.navigateTo({ url: "/pages/profile/wx-auth" });
}

function onAvatarError() {
  // 本地临时路径 + 网络地址都加载失败时，退回首字占位图，避免留一片空白
  avatarBroken.value = true;
}

function onBirthday(e) {
  form.value.birthday = e.detail.value;
}
function onActivity(e) {
  form.value.activity_level = Number(e.detail.value) + 1;
}

async function save() {
  const payload = {
    gender: form.value.gender,
    activity_level: form.value.activity_level,
  };
  if (form.value.birthday) payload.birthday = form.value.birthday;
  if (form.value.height_cm) payload.height_cm = Number(form.value.height_cm);

  await user.saveProfile(payload);
  uni.showToast({ title: "已保存", icon: "success" });
  await load();
}

function goGoal() {
  uni.navigateTo({ url: "/pages/profile/goal" });
}
function goCustom() {
  uni.navigateTo({ url: "/pages/record/food-custom" });
}
function exportCsv() {
  const root = BASE_URL.replace(/\/api\/v1\/?$/, "");
  uni.showLoading({ title: "导出中" });
  uni.downloadFile({
    url: `${root}/api/v1/export/records.csv?days=365`,
    header: { Authorization: `Bearer ${uni.getStorageSync("token")}` },
    success: (res) => {
      if (res.statusCode === 200) {
        uni.openDocument({
          filePath: res.tempFilePath,
          showMenu: true,
          fail: () => uni.showToast({ title: "当前环境无法预览文件", icon: "none" }),
        });
      } else {
        uni.showToast({ title: "导出失败", icon: "none" });
      }
    },
    fail: () => uni.showToast({ title: "网络错误", icon: "none" }),
    complete: () => uni.hideLoading(),
  });
}
function logout() {
  uni.showModal({
    title: "退出登录",
    content: "确定要退出吗？本地记录不会丢失",
    success: (r) => {
      if (r.confirm) {
        user.logout();
        uni.showToast({ title: "已退出", icon: "none" });
        setTimeout(() => uni.reLaunch({ url: "/pages/index/index" }), 500);
      }
    },
  });
}

// 每日打卡提醒：开启 = 申请一次性订阅授权 → 上报 grant → 打开开关
// 注意 requestSubscribeMessage 必须在用户点击回调里同步调用（不能先 await），
// 所以模板 ID 在页面加载时就预取好了
function onRemind() {
  if (!remind.value.template_id) {
    uni.showToast({ title: "提醒功能暂未配置模板", icon: "none" });
    return;
  }
  if (remind.value.enabled) {
    uni.showModal({
      title: "关闭提醒",
      content: `不再发送每天 ${remind.value.remind_time} 的打卡提醒？`,
      success: async (r) => {
        if (r.confirm) {
          remind.value = await subscribeApi.toggle(false);
          uni.showToast({ title: "已关闭", icon: "none" });
        }
      },
    });
    return;
  }
  uni.requestSubscribeMessage({
    tmplIds: [remind.value.template_id],
    success: async (res) => {
      try {
        if (res[remind.value.template_id] === "accept") {
          await subscribeApi.grant();
        }
      } catch (e) {
        console.error(e);
      }
      remind.value = await subscribeApi.toggle(true);
      uni.showToast({ title: "已开启", icon: "success" });
    },
    fail: () => uni.showToast({ title: "未完成订阅授权", icon: "none" }),
  });
}

async function load() {
  try {
    await user.ensureLogin();
    // 每次进页强制刷新微信资料（昵称/头像可能在授权页被改过）
    await user.loadProfile();
    // 头像网络图下载为本地路径，避免 <image> 加载 http 失败
    avatarBroken.value = false;
    await user.loadAvatarLocal();
    const p = user.profile;
    if (p) {
      form.value = {
        gender: p.gender || 1,
        birthday: p.birthday || "",
        height_cm: p.height_cm ? String(p.height_cm) : "",
        activity_level: p.activity_level || 1,
      };
    }
    const [g, pl, ov] = await Promise.all([
      authApi.getGoal(),
      statsApi.plan(),
      statsApi.overview(),
    ]);
    goal.value = g;
    plan.value = pl;
    overview.value = ov;

    // 打卡提醒状态 + 模板 ID（供点击时同步调用 requestSubscribeMessage）
    try {
      const [st, cfg] = await Promise.all([
        subscribeApi.status(),
        subscribeApi.config(),
      ]);
      remind.value = { ...st, template_id: cfg.template_id || "" };
    } catch (e) {
      console.error(e);
    }
  } catch (e) {
    console.error(e);
  }
}

onShow(load);
</script>

<style scoped lang="scss">
.page {
  padding: 24rpx 0 60rpx;
}

/* ============ 顶部个人主页 ============ */
.profile-hero {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 52rpx 32rpx 44rpx;
  margin: 24rpx 24rpx 0;
  background: linear-gradient(180deg, #eafaf1 0%, #f6fcf8 55%, var(--card) 100%);
  border: 1rpx solid #d4ecdf;
  border-radius: var(--r-lg);
  box-shadow: var(--shadow-card);
}
.hero-avatar {
  width: 184rpx;
  height: 184rpx;
  border-radius: 50%;
  background: #fff;
  border: 6rpx solid #fff;
  box-shadow: 0 16rpx 44rpx rgba(14, 158, 104, 0.18);
  flex-shrink: 0;
}
.hero-avatar-ph {
  display: flex;
  align-items: center;
  justify-content: center;
  &.boy {
    background: linear-gradient(135deg, #22bd85, #0d9a63);
  }
  &.girl {
    background: linear-gradient(135deg, #5da9e6, #3d83c4);
  }
  .hero-avatar-char {
    font-size: 80rpx;
    font-weight: 700;
    color: #fff;
  }
}
.hero-name-row {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-top: 24rpx;
  gap: 10rpx;
}
.hero-name {
  font-size: 42rpx;
  font-weight: 700;
  color: var(--ink);
  max-width: 60vw;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  line-height: 1.2;
}
.hero-stat {
  margin-top: 14rpx;
  font-size: 24rpx;
  color: var(--ink-3);
}

/* 个人资料入口卡片(只包一个菜单项,保持清爽) */
.menu-card {
  padding: 12rpx 32rpx;
}

/* ============ 卡片 ============ */
.card {
  background: var(--card);
  border-radius: var(--r-lg);
  padding: 30rpx 32rpx;
  margin: 24rpx 24rpx 0;
  box-shadow: var(--shadow-card);
}
.card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30rpx;
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

/* ============ 表单 ============ */
.field {
  margin-bottom: 28rpx;
}
.field-row {
  display: flex;
  gap: 24rpx;
}
.flex1 {
  flex: 1;
  min-width: 0;
}
.label {
  display: block;
  font-size: 24rpx;
  font-weight: 500;
  color: var(--ink-2);
  margin-bottom: 14rpx;
}
.seg {
  display: flex;
  background: #edf3ef;
  border-radius: 999rpx;
  padding: 8rpx;
}
.seg-item {
  flex: 1;
  text-align: center;
  padding: 22rpx 0;
  border-radius: 999rpx;
  font-size: 28rpx;
  color: var(--ink-3);
  transition: all 0.2s;
  &.on {
    background: #fff;
    color: var(--brand-deep);
    font-weight: 600;
    box-shadow: 0 6rpx 16rpx rgba(20, 94, 62, 0.1);
  }
}
.picker {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 88rpx;
  background: #f1f6f3;
  border: 1rpx solid #e3ece6;
  border-radius: var(--r-md);
  padding: 0 26rpx;
  font-size: 30rpx;
  color: var(--ink);
  box-sizing: border-box;
  &.empty {
    color: var(--ink-4);
  }
}
.chev-r {
  color: var(--ink-4);
  font-size: 32rpx;
}
.input-wrap {
  position: relative;
}
.input {
  height: 88rpx;
  width: 100%;
  background: #f1f6f3;
  border: 1rpx solid #e3ece6;
  border-radius: var(--r-md);
  padding: 0 26rpx;
  font-size: 30rpx;
  color: var(--ink);
  box-sizing: border-box;
}
.unit-suffix {
  position: absolute;
  right: 26rpx;
  top: 50%;
  transform: translateY(-50%);
  font-size: 26rpx;
  color: var(--ink-3);
  font-weight: 500;
}
.btn {
  width: 100%;
  height: 96rpx;
  border-radius: 999rpx;
  background: var(--grad-brand);
  color: #fff;
  font-size: 32rpx;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-top: 12rpx;
  box-shadow: var(--shadow-btn);
}
button.btn {
  line-height: 96rpx;
}

/* ============ 目标 ============ */
.link-chip {
  font-size: 24rpx;
  font-weight: 500;
  color: var(--brand-deep);
  background: var(--brand-tint);
  padding: 10rpx 26rpx;
  border-radius: 999rpx;
}
.goal-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10rpx 0;
}
.goal-item {
  flex: 1;
  text-align: center;
}
.goal-circle {
  width: 128rpx;
  height: 128rpx;
  border-radius: 50%;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: center;
  &.start {
    background: var(--amber-tint);
    border: 6rpx solid #f6e3bd;
  }
  &.target {
    background: var(--brand-tint);
    border: 6rpx solid #c9ecd9;
  }
  .gv {
    font-size: 40rpx;
    font-weight: 700;
    color: var(--ink);
  }
}
.gl {
  display: block;
  font-size: 22rpx;
  color: var(--ink-3);
  margin-top: 14rpx;
}
.goal-flow {
  flex: 0 0 190rpx;
  text-align: center;
  .flow-arrow {
    display: block;
    font-size: 40rpx;
    color: var(--brand);
    line-height: 1;
  }
  .flow-tag {
    display: inline-block;
    margin-top: 10rpx;
    font-size: 22rpx;
    color: var(--brand-deep);
    background: var(--brand-tint);
    padding: 6rpx 16rpx;
    border-radius: 999rpx;
    font-weight: 600;
  }
  .ft-unit {
    font-weight: 400;
  }
}
.empty-goal {
  text-align: center;
  padding: 20rpx 0 8rpx;
  .eg-main {
    display: block;
    font-size: 28rpx;
    font-weight: 500;
    color: var(--ink-2);
  }
  .eg-sub {
    display: block;
    font-size: 22rpx;
    color: var(--ink-4);
    margin-top: 10rpx;
  }
  .eg-btn {
    display: inline-block;
    margin-top: 26rpx;
    font-size: 26rpx;
    font-weight: 500;
    color: #fff;
    background: var(--grad-brand);
    padding: 16rpx 48rpx;
    border-radius: 999rpx;
    box-shadow: var(--shadow-btn);
  }
}

/* ============ 测算 ============ */
.plan-grid {
  display: flex;
  align-items: stretch;
}
.plan-item {
  flex: 1;
  text-align: center;
  display: flex;
  flex-direction: column;
  justify-content: center;
  .pv {
    font-size: 40rpx;
    font-weight: 700;
    color: var(--ink);
  }
  .pl {
    font-size: 20rpx;
    color: var(--ink-3);
    margin-top: 10rpx;
  }
  &.hl {
    background: var(--brand-tint);
    border-radius: var(--r-md);
    padding: 20rpx 8rpx;
    .pv {
      color: var(--brand-deep);
    }
    .pl {
      color: var(--brand-deep);
      font-weight: 500;
    }
  }
}
.plan-sep {
  width: 1rpx;
  margin: 8rpx 22rpx;
  background: var(--line);
}
.plan-note {
  display: flex;
  align-items: flex-start;
  margin-top: 24rpx;
  background: #f5f9f6;
  border-radius: var(--r-sm);
  padding: 18rpx 22rpx;
  font-size: 22rpx;
  color: var(--ink-3);
  line-height: 1.6;
  .note-ico {
    margin-right: 10rpx;
  }
}

/* ============ 概览 ============ */
.stat-grid {
  display: flex;
}
.stat {
  flex: 1;
  text-align: center;
  .sv {
    display: block;
    font-size: 44rpx;
    font-weight: 700;
    color: var(--ink);
    &.hl {
      color: var(--brand-deep);
    }
  }
  .sl {
    display: block;
    font-size: 20rpx;
    color: var(--ink-3);
    margin-top: 10rpx;
  }
}

/* ============ 菜单 ============ */
.menu {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 22rpx 0;
  &:not(:last-child) {
    border-bottom: 1rpx solid var(--line);
  }
}
.menu-left {
  display: flex;
  align-items: center;
  flex: 1;
}
.menu-ico {
  width: 68rpx;
  height: 68rpx;
  border-radius: 20rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32rpx;
  margin-right: 22rpx;
  flex-shrink: 0;
  &.bell {
    background: var(--amber-tint);
  }
  &.food {
    background: var(--brand-tint);
  }
  &.data {
    background: var(--blue-tint);
  }
  &.profile {
    background: #f0f7f3;
  }
}
.menu-txt {
  flex: 1;
}
.menu-title {
  display: block;
  font-size: 28rpx;
  color: var(--ink);
}
.menu-sub {
  display: block;
  font-size: 20rpx;
  color: var(--ink-4);
  margin-top: 4rpx;
  &.on {
    color: var(--brand-deep);
  }
}
.menu-right {
  .switch {
    width: 88rpx;
    height: 50rpx;
    border-radius: 999rpx;
    background: #d8e2dc;
    padding: 4rpx;
    box-sizing: border-box;
    transition: background 0.25s;
    &.on {
      background: var(--grad-brand);
    }
    .knob {
      width: 42rpx;
      height: 42rpx;
      border-radius: 50%;
      background: #fff;
      box-shadow: 0 2rpx 6rpx rgba(0, 0, 0, 0.15);
      transition: transform 0.25s;
    }
    &.on .knob {
      transform: translateX(38rpx);
    }
  }
}
.menu-arrow {
  color: var(--ink-4);
  font-size: 40rpx;
  margin-left: 12rpx;
  transition: transform 0.25s;
  &.open {
    transform: rotate(90deg);
  }
}
.card-hint {
  display: block;
  font-size: 20rpx;
  color: var(--ink-4);
  margin-top: 14rpx;
  line-height: 1.6;
  background: #f5f9f6;
  border-radius: var(--r-sm);
  padding: 16rpx 20rpx;
}

/* 退出 */
.logout {
  margin: 48rpx 60rpx 0;
  text-align: center;
  font-size: 28rpx;
  font-weight: 500;
  color: var(--red);
  background: #fff;
  border-radius: 999rpx;
  padding: 26rpx 0;
  box-shadow: var(--shadow-card);
}
.disclaimer {
  margin: 24rpx 32rpx 0;
  font-size: 20rpx;
  color: var(--ink-4);
  text-align: center;
}
</style>
