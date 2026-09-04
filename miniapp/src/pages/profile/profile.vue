<template>
  <view class="page">
    <!-- ============ 顶部个人主页（横向排布，170px 级 → 190rpx 级） ============ -->
    <view class="profile-hero">
      <!-- #ifdef MP-WEIXIN -->
      <!-- 微信官方 chooseAvatar 按钮：点击后弹出系统级头像选择器(含微信头像缩略图 / 相册 / 拍照) -->
      <button
        class="hero-avatar-btn hit"
        open-type="chooseAvatar"
        @chooseavatar="onChooseWechatAvatar"
      >
        <image
          v-if="user.avatarSrc && !avatarBroken"
          class="hero-avatar-img"
          :src="user.avatarSrc"
          mode="aspectFill"
          aria-label="用户头像"
          @error="onAvatarError"
        />
        <view v-else class="hero-avatar hero-avatar-ph" :class="genderClass">
          <text class="hero-avatar-char">{{ user.displayName.slice(0, 1) }}</text>
        </view>
      </button>
      <!-- #endif -->
      <!-- #ifndef MP-WEIXIN -->
      <view class="hero-avatar-wrap hit">
        <image
          v-if="user.avatarSrc && !avatarBroken"
          class="hero-avatar"
          :src="user.avatarSrc"
          mode="aspectFill"
          aria-label="用户头像"
          @error="onAvatarError"
          @click="onAlbumAvatar"
        />
        <view
          v-else
          class="hero-avatar hero-avatar-ph"
          :class="genderClass"
          @click="onAlbumAvatar"
        >
          <text class="hero-avatar-char">{{ user.displayName.slice(0, 1) }}</text>
        </view>
      </view>
      <!-- #endif -->
      <view class="hero-body">
        <view class="hero-name-row" @click="onNicknameTap">
          <template v-if="!editingNickname">
            <text class="hero-name">{{ user.displayName }}</text>
          </template>
          <!-- 微信官方 nickname input：点击后键盘上方自动展示「用微信昵称」快捷填充 -->
          <input
            v-else
            class="hero-name-input"
            type="nickname"
            v-model="nicknameDraft"
            @blur="saveNickname"
            confirm-type="done"
            focus
          />
          <text class="hero-save-chip" v-if="editingNickname" @click.stop="saveNickname">保存</text>
        </view>
        <text class="hero-stat">累计记录 <text class="num hl">{{ overview ? overview.recorded_days : 0 }}</text> 天<text v-if="overview && overview.streak_days"> · 连续 <text class="num">{{ overview.streak_days }}</text> 天</text></text>
      </view>
      <text class="hero-arrow">›</text>
    </view>

    <view class="grp">目标与测算</view>
    <view class="card menu-list-card">
      <view class="menu" @click="goInfo"><view class="menu-left"><view class="menu-ico profile">📝</view><view class="menu-txt"><text class="menu-title">个人资料</text><text class="menu-sub">{{ profileSummary }}</text></view></view><text class="status-pill" v-if="!profileDone">去完善</text><text class="menu-arrow">›</text></view>
      <view class="menu" @click="goGoal"><view class="menu-left"><view class="menu-ico goal">🎯</view><view class="menu-txt"><text class="menu-title">减重目标</text><text class="menu-sub">{{ hasGoal ? `${goal.start_weight} → ${goal.target_weight} kg` : "设置你的目标体重" }}</text></view></view><text class="status-pill">{{ hasGoal ? "进行中" : "去设置" }}</text><text class="menu-arrow">›</text></view>
      <view class="menu" @click="goPlan"><view class="menu-left"><view class="menu-ico calorie">🔥</view><view class="menu-txt"><text class="menu-title">我的热量测算</text><text class="menu-sub">{{ planSub }}</text></view></view><text class="menu-arrow">›</text></view>
    </view>

    <view class="grp">数据与设置</view>
    <view class="card menu-list-card">
      <view class="menu" @click="showHealthTip"><view class="menu-left"><view class="menu-ico health">🩺</view><view class="menu-txt"><text class="menu-title">我的健康档案</text><text class="menu-sub">{{ hasGoal ? `BMI、体脂率、腰围变化` : "BMI、体脂率、腰围变化" }}</text></view></view><text class="menu-arrow">›</text></view>
      <view class="menu" @click="exportCsv"><view class="menu-left"><view class="menu-ico data">📊</view><view class="menu-txt"><text class="menu-title">导出数据（CSV）</text><text class="menu-sub">把记录带走，随时可查</text></view></view><text class="menu-arrow">›</text></view>
      <view class="menu" @click="onRemind" role="button" aria-label="每日记录提醒开关"><view class="menu-left"><view class="menu-ico bell">🔔</view><view class="menu-txt"><text class="menu-title">每日记录提醒</text><text class="menu-sub" :class="{ on: remind.enabled }">{{ remindText }}</text></view></view><view class="menu-right"><view class="switch" :class="{ on: remind.enabled }" role="switch" :aria-checked="remind.enabled"><view class="knob" /></view></view></view>
      <view class="menu" @click="showHelp"><view class="menu-left"><view class="menu-ico help">❓</view><view class="menu-txt"><text class="menu-title">使用帮助</text><text class="menu-sub">记录和目标设置说明</text></view></view><text class="menu-arrow">›</text></view>
    </view>

    <view class="logout hit" @click="logout">退出登录</view>
    <view class="disclaimer">本工具仅用于个人数据记录,不构成医疗建议</view>
    <view class="safearea" />
  </view>
</template>

<script setup>
import { ref, computed } from "vue";
import { onShow } from "@dcloudio/uni-app";
import { authApi, statsApi, subscribeApi } from "@/api";
import { BASE_URL } from "@/api/request";
import { useUserStore } from "@/store/user";
import { today } from "@/utils/date";
import { theme, setTheme, applyTheme } from "@/utils/theme";

const user = useUserStore();
const todayStr = today(); // 本地时区的今天（toISOString 是 UTC，凌晨会差一天）

const activityLabels = ["久坐少动", "轻度活动", "中度活动", "高活动量", "运动员级"];

const form = ref({ gender: 1, birthday: "", height_cm: "", activity_level: 1 });
const goal = ref(null);
const plan = ref(null);
const overview = ref(null);
// 昵称就地编辑：点 hero-name-row 切换到 input，失焦或点保存 chip 提交
const editingNickname = ref(false);
const nicknameDraft = ref("");
const nicknameSaving = ref(false);
// 头像就地编辑保存中的标志
const avatarSaving = ref(false);
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
// 「个人资料」菜单项摘要：性别 · 年龄 · 身高 · 活动量
const profileDone = computed(() => !!(form.value.gender && form.value.height_cm));
const profileSummary = computed(() => {
  const f = form.value;
  const parts = [];
  parts.push(f.gender === 2 ? "女" : f.gender === 1 ? "男" : "未填性别");
  if (f.birthday) {
    const b = new Date(f.birthday);
    const t = new Date();
    let age = t.getFullYear() - b.getFullYear();
    if (t.getMonth() + 1 < b.getMonth() + 1 || (t.getMonth() + 1 === b.getMonth() + 1 && t.getDate() < b.getDate())) age--;
    parts.push(Math.max(age, 0) + "岁");
  }
  if (f.height_cm) parts.push(f.height_cm + "cm");
  parts.push(activityLabels[f.activity_level - 1] || activityLabels[0]);
  return parts.join(" · ");
});
// 资料不全时 plan.bmr 为 null，直接用 Math.round 会抛错，这里统一兜底
const planSub = computed(() => {
  const p = plan.value;
  if (!p || p.bmr == null || p.tdee == null) return "补全资料后自动测算每日预算";
  return `BMR ${Math.round(p.bmr)} · TDEE ${Math.round(p.tdee)} 千卡`;
});
const lostText = computed(() => {
  const v = overview.value?.total_lost;
  return v == null ? "--" : Number(v).toFixed(1);
});

// 微信 chooseAvatar 回调：用户从官方面板选了头像（含微信头像 / 相册 / 拍照），立即上传保存
function onChooseWechatAvatar(e) {
  if (e.detail && e.detail.avatarUrl) saveAvatar(e.detail.avatarUrl);
}
// 非 MP-WEIXIN 平台没有 chooseAvatar，提供简单的相册选择
function onAlbumAvatar() {
  if (typeof uni.chooseMedia === "function") {
    uni.chooseMedia({
      count: 1,
      mediaType: ["image"],
      sourceType: ["album", "camera"],
      sizeType: ["compressed"],
      success: (res) => {
        const f = res.tempFiles && res.tempFiles[0];
        if (f && (f.tempFilePath || f.path)) saveAvatar(f.tempFilePath || f.path);
      },
    });
    return;
  }
  uni.chooseImage({
    count: 1,
    sizeType: ["compressed"],
    sourceType: ["album", "camera"],
    success: (r) => saveAvatar(r.tempFilePaths && r.tempFilePaths[0]),
  });
}
async function saveAvatar(tempPath) {
  if (!tempPath) return;
  if (avatarSaving.value) return;
  avatarSaving.value = true;
  try {
    await user.ensureLogin();
    const profile = await authApi.uploadAvatar(tempPath);
    user.resetAvatarLocal();
    if (profile) user.profile = profile;
    await user.loadAvatarLocal();
    avatarBroken.value = false;
    uni.showToast({ title: "头像已更新", icon: "success" });
  } catch (e) {
    console.error(e);
    uni.showToast({ title: "头像更新失败", icon: "none" });
  } finally {
    avatarSaving.value = false;
  }
}
// 点昵称 → 就地切换成输入框
function onNicknameTap() {
  if (editingNickname.value) return;
  nicknameDraft.value = user.profile?.nickname || "";
  editingNickname.value = true;
}
async function saveNickname() {
  // 失焦触发，draft 已更新；防重复：若不在编辑态直接返回
  if (!editingNickname.value) return;
  const nick = nicknameDraft.value.trim();
  if (!nick) {
    editingNickname.value = false;
    uni.showToast({ title: "昵称不能为空", icon: "none" });
    return;
  }
  if (nick === (user.profile?.nickname || "")) {
    editingNickname.value = false;
    return;
  }
  nicknameSaving.value = true;
  try {
    await user.ensureLogin();
    const profile = await user.saveProfile({ nickname: nick });
    if (profile) user.profile = profile;
    editingNickname.value = false;
    uni.showToast({ title: "昵称已更新", icon: "success" });
  } catch (e) {
    console.error(e);
    uni.showToast({ title: "昵称保存失败", icon: "none" });
  } finally {
    nicknameSaving.value = false;
  }
}

function onAvatarError() {
  // 本地临时路径 + 网络地址都加载失败时，退回首字占位图，避免留一片空白
  avatarBroken.value = true;
}

function goGoal() {
  uni.navigateTo({ url: "/pages/profile/goal" });
}
function goInfo() {
  uni.navigateTo({ url: "/pages/profile/info" });
}
function goPlan() {
  uni.navigateTo({ url: "/pages/profile/plan" });
}
function goCustom() {
  uni.navigateTo({ url: "/pages/record/food-custom" });
}
function showHealthTip() {
  uni.showToast({ title: "健康档案功能即将上线", icon: "none" });
}
function showHelp() {
  uni.showModal({
    title: "使用帮助",
    content: "每天记录体重和饮食，系统会根据你的目标生成热量预算与趋势数据。",
    showCancel: false,
  });
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

onShow(() => {
  load();
  applyTheme(); // 进入本页时同步深色类（导航回来也保持）
});

function toggleTheme() {
  setTheme(theme.value === "dark" ? "light" : "dark");
}
</script>

<style scoped lang="scss">
.page {
  padding: 24rpx 0 64rpx;
}

/* ============ 顶部个人主页（横向，压缩头部高度） ============ */
.profile-hero {
  display: flex;
  align-items: center;
  gap: 24rpx;
  padding: 32rpx;
  margin: var(--gap-card) var(--pad-x) 0;
  background: var(--card);
  border: 1rpx solid var(--line);
  border-radius: var(--r-lg);
  box-shadow: var(--shadow-card);
}
.hero-avatar {
  width: 128rpx;
  height: 128rpx;
  border-radius: 50%;
  background: var(--card);
  border: 6rpx solid var(--card);
  box-shadow: 0 8rpx 24rpx rgba(6, 121, 76, 0.20);
  flex-shrink: 0;
}
/* MP-WEIXIN 下：把头像包在 chooseAvatar 按钮里（按钮透明，保留系统面板能力） */
.hero-avatar-btn {
  margin: 0;
  padding: 0;
  border-radius: 50%;
  line-height: 1;
  background: transparent;
  border: none;
  overflow: visible;
  flex-shrink: 0;
}
button.hero-avatar-btn::after { display: none; }
.hero-avatar-img {
  width: 128rpx;
  height: 128rpx;
  border-radius: 50%;
  background: var(--card);
  border: 6rpx solid var(--card);
  box-shadow: 0 8rpx 24rpx rgba(6, 121, 76, 0.20);
  display: block;
}
.hero-avatar-wrap {
  display: flex;
  align-items: center;
  flex-shrink: 0;
}
.hero-avatar-ph {
  display: flex;
  align-items: center;
  justify-content: center;
  &.boy {
    background: var(--grad-brand);
  }
  &.girl {
    background: var(--grad-blue);
  }
  .hero-avatar-char {
    font-size: 56rpx;
    font-weight: 700;
    color: var(--on-brand);
  }
}
.hero-body {
  flex: 1;
  min-width: 0;
}
.hero-name-row {
  display: flex;
  align-items: center;
  gap: 12rpx;
}
.hero-name {
  font-size: 36rpx;
  font-weight: 700;
  color: var(--ink);
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  line-height: 1.2;
  letter-spacing: -0.4rpx;
}
.hero-stat {
  display: block;
  margin-top: 6rpx;
  font-size: 23rpx;
  color: var(--ink-3);
  font-variant-numeric: tabular-nums;
  .hl { color: var(--brand); font-weight: 700; }
  .num { font-variant-numeric: tabular-nums; }
}
.hero-arrow {
  font-size: 38rpx;
  color: var(--line-strong);
  flex-shrink: 0;
}

/* 分组标题 */
.grp {
  font-size: 23rpx;
  font-weight: 700;
  color: var(--ink-3);
  letter-spacing: 0.6rpx;
  padding: 32rpx 32rpx 16rpx;
}

/* 底部安全区：避免 iPhone 横条压住最后一项 */
.safearea {
  height: 24rpx;
}

/* 昵称就地编辑：input 形态 + 行内"保存"chip */
.hero-name-input {
  font-size: 42rpx;
  font-weight: 700;
  color: var(--ink);
  background: var(--card);
  border: 1rpx solid var(--line);
  border-radius: 12rpx;
  padding: 6rpx 16rpx;
  width: 320rpx;
  text-align: center;
  height: 56rpx;
  line-height: 56rpx;
}
.hero-save-chip {
  font-size: 22rpx;
  font-weight: 600;
  color: var(--on-brand);
  background: var(--grad-brand);
  padding: 8rpx 24rpx;
  border-radius: var(--r-pill);
  margin-left: 12rpx;
  flex-shrink: 0;
  box-shadow: var(--shadow-btn);
}

/* 个人资料入口卡片(只包一个菜单项,保持清爽) */
.menu-card {
  padding: 12rpx 32rpx;
}
.menu-list-card {
  padding: 0 32rpx;
  overflow: hidden;
}
/* ============ 卡片 ============ */
.card {
  background: var(--card);
  border-radius: var(--r-lg);
  padding: var(--pad-card);
  margin: var(--gap-card) var(--pad-x) 0;
  box-shadow: var(--shadow-card);
}
.card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32rpx;
}
.head-l {
  display: flex;
  align-items: center;
}
.head-dot {
  width: 14rpx;
  height: 14rpx;
  border-radius: 50%;
  margin-right: 12rpx;
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
  margin-bottom: 24rpx;
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
  margin-bottom: 12rpx;
}
.seg {
  display: flex;
  background: var(--surface-2);
  border-radius: var(--r-pill);
  padding: 8rpx;
}
.seg-item {
  flex: 1;
  text-align: center;
  padding: 20rpx 0;
  border-radius: var(--r-pill);
  font-size: 28rpx;
  color: var(--ink-3);
  transition: all 0.2s;
  &.on {
    background: var(--card);
    color: var(--brand-deep);
    font-weight: 600;
    box-shadow: var(--shadow-card);
  }
}
.picker {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 88rpx;
  background: var(--surface-2);
  border: 1rpx solid var(--line);
  border-radius: var(--r-md);
  padding: 0 24rpx;
  font-size: 30rpx;
  color: var(--ink);
  box-sizing: border-box;
  &.empty {
    color: var(--ink-3);
  }
}
.chev-r {
  color: var(--ink-3);
  font-size: 32rpx;
}
.input-wrap {
  position: relative;
}
.input {
  height: 88rpx;
  width: 100%;
  background: var(--surface-2);
  border: 1rpx solid var(--line);
  border-radius: var(--r-md);
  padding: 0 24rpx;
  font-size: 30rpx;
  color: var(--ink);
  box-sizing: border-box;
}
.unit-suffix {
  position: absolute;
  right: 24rpx;
  top: 50%;
  transform: translateY(-50%);
  font-size: 26rpx;
  color: var(--ink-3);
  font-weight: 500;
}
.btn {
  width: 100%;
  height: 96rpx;
  border-radius: var(--r-pill);
  background: var(--grad-brand);
  color: var(--on-brand);
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
  padding: 8rpx 24rpx;
  border-radius: var(--r-pill);
}
.goal-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8rpx 0;
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
    border: 6rpx solid var(--amber-fill);
  }
  &.target {
    background: var(--brand-tint);
    border: 6rpx solid var(--brand);
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
  margin-top: 12rpx;
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
    margin-top: 8rpx;
    font-size: 22rpx;
    color: var(--brand-deep);
    background: var(--brand-tint);
    padding: 6rpx 16rpx;
    border-radius: var(--r-pill);
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
    color: var(--ink-3);
    margin-top: 8rpx;
  }
  .eg-btn {
    display: inline-block;
    margin-top: 24rpx;
    font-size: 26rpx;
    font-weight: 500;
    color: var(--on-brand);
    background: var(--grad-brand);
    padding: 16rpx 48rpx;
    border-radius: var(--r-pill);
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
    margin-top: 8rpx;
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
  margin: 8rpx 20rpx;
  background: var(--line);
}
.plan-note {
  display: flex;
  align-items: flex-start;
  margin-top: 24rpx;
  background: var(--surface-2);
  border-radius: var(--r-sm);
  padding: 16rpx 20rpx;
  font-size: 22rpx;
  color: var(--ink-3);
  line-height: 1.6;
  .note-ico {
    margin-right: 8rpx;
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
    margin-top: 8rpx;
  }
}

/* ============ 菜单 ============ */
.menu {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20rpx 0;
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
  margin-right: 20rpx;
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
    background: var(--surface-2);
  }
  &.goal { background: var(--red-tint); }
  &.calorie { background: var(--amber-tint); }
  &.health { background: var(--blue-tint); }
  &.help { background: var(--red-tint); }
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
  color: var(--ink-3);
  margin-top: 4rpx;
  &.on {
    color: var(--brand-deep);
  }
}
.menu-right {
  .switch {
    width: 88rpx;
    height: 50rpx;
    border-radius: var(--r-pill);
    background: var(--line-strong);
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
      background: var(--card);
      box-shadow: 0 2rpx 6rpx rgba(0, 0, 0, 0.15);
      transition: transform 0.25s;
    }
    &.on .knob {
      transform: translateX(38rpx);
    }
  }
}
.menu-arrow {
  color: var(--ink-3);
  font-size: 40rpx;
  margin-left: 12rpx;
  transition: transform 0.25s;
  &.open {
    transform: rotate(90deg);
  }
}
.status-pill {
  flex-shrink: 0;
  color: var(--brand);
  background: var(--brand-tint);
  font-size: 21rpx;
  font-weight: 700;
  padding: 6rpx 14rpx;
  border-radius: var(--r-pill);
}
.card-hint {
  display: block;
  font-size: 20rpx;
  color: var(--ink-3);
  margin-top: 12rpx;
  line-height: 1.6;
  background: var(--surface-2);
  border-radius: var(--r-sm);
  padding: 16rpx 20rpx;
}

/* 退出 */
.logout {
  margin: 48rpx 64rpx 0;
  text-align: center;
  font-size: 28rpx;
  font-weight: 500;
  color: var(--red);
  background: var(--card);
  border-radius: var(--r-pill);
  padding: 24rpx 0;
  box-shadow: var(--shadow-card);
}
.disclaimer {
  margin: 24rpx var(--pad-x) 0;
  font-size: 20rpx;
  color: var(--ink-3);
  text-align: center;
}
</style>
