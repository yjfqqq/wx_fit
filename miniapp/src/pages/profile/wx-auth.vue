<template>
  <view class="page">
    <view class="card">
      <view class="head">
        <text class="title">用微信身份开启记录</text>
        <text class="sub">授权后头像昵称将用于小程序展示,可随时修改</text>
      </view>

      <!-- 头像选择(微信官方 chooseAvatar 按钮,仅微信端) -->
      <view class="field center">
        <text class="label">微信头像</text>
        <!-- #ifdef MP-WEIXIN -->
        <button class="avatar-btn" open-type="chooseAvatar" @chooseavatar="onChooseAvatar">
          <image v-if="avatarUrl" class="avatar-img" :src="avatarUrl" mode="aspectFill" />
          <view v-else class="avatar-ph">
            <text class="ph-plus">＋</text>
          </view>
        </button>
        <!-- #endif -->
        <!-- #ifndef MP-WEIXIN -->
        <view class="avatar-ph-static" @click="onPickAvatarH5">
          <image v-if="avatarUrl" class="avatar-img" :src="avatarUrl" mode="aspectFill" />
          <view v-else class="avatar-ph">
            <text class="ph-plus">＋</text>
          </view>
        </view>
        <!-- #endif -->
        <text class="tip">{{ avatarUrl ? "点击可更换" : "点击选择微信头像" }}</text>
      </view>

      <!-- 昵称(微信官方 nickname 输入) -->
      <view class="field">
        <text class="label">微信昵称</text>
        <input
          class="nick-input"
          type="nickname"
          v-model="nickname"
          placeholder="输入昵称或使用微信昵称"
          placeholder-class="ph"
        />
      </view>

      <view class="field">
        <view class="info-row">
          <text class="info-item">· 登录后数据自动关联微信账号</text>
          <text class="info-item">· 头像仅用于小程序内展示</text>
        </view>
      </view>

      <button class="btn" :class="{ disabled: !canSave, loading: saving }" :disabled="!canSave || saving" @click="onSave">
        {{ saving ? "保存中..." : "确定" }}
      </button>
    </view>
  </view>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { authApi } from "@/api";
import { useUserStore } from "@/store/user";

const user = useUserStore();
const avatarTemp = ref("");
const avatarUrl = ref("");
const nickname = ref("");
const saving = ref(false);

const canSave = computed(() => !!nickname.value.trim());

onMounted(async () => {
  try {
    await user.ensureLogin();
  } catch (e) {
    uni.showToast({ title: "登录失败，请重试", icon: "none" });
  }
  // 已有资料时回填（头像走本地下载，避免 <image> 加载 http 网络图失败）
  if (user.profile?.avatar_url) {
    await user.loadAvatarLocal();
    avatarUrl.value = user.avatarSrc;
  }
  if (user.profile?.nickname) nickname.value = user.profile.nickname;
});

function onChooseAvatar(e) {
  const p = e.detail.avatarUrl;
  if (!p) return;
  avatarTemp.value = p;
  avatarUrl.value = p;
}

// H5/其它端没有 chooseAvatar,用相册/相机选择做兜底
function onPickAvatarH5() {
  // #ifndef MP-WEIXIN
  uni.chooseImage({
    count: 1,
    sizeType: ["compressed"],
    sourceType: ["album", "camera"],
    success: (r) => {
      const p = r.tempFilePaths && r.tempFilePaths[0];
      if (!p) return;
      avatarTemp.value = p;
      avatarUrl.value = p;
    },
  });
  // #endif
}

async function onSave() {
  const nick = nickname.value.trim();
  if (!nick) {
    uni.showToast({ title: "请填写昵称", icon: "none" });
    return;
  }
  if (!avatarUrl.value) {
    uni.showToast({ title: "请选择微信头像", icon: "none" });
    return;
  }
  saving.value = true;
  try {
    await user.ensureLogin();

    // 1) 若选了新头像 → 上传，后端返回完整 profile
    let profile = null;
    if (avatarTemp.value) {
      profile = await authApi.uploadAvatar(avatarTemp.value);
      // 换新头像后清掉本地缓存下载，让「我的」页按新地址重新下载
      user.resetAvatarLocal();
    }
    // 2) 更新昵称
    if (nick !== (user.profile?.nickname || "")) {
      profile = await user.saveProfile({ nickname: nick });
    }
    if (profile) user.profile = profile;
    else if (user.profile) user.profile = { ...user.profile, nickname: nick };

    // 提前下载新头像到本地，返回「我的」页立即可显示
    if (user.profile?.avatar_url) {
      await user.loadAvatarLocal().catch(() => {});
    }

    uni.showToast({ title: "授权成功", icon: "success" });
    setTimeout(() => uni.navigateBack(), 500);
  } catch (e) {
    console.error(e);
    uni.showToast({ title: "保存失败，请重试", icon: "none" });
  } finally {
    saving.value = false;
  }
}
</script>

<style scoped lang="scss">
.page {
  min-height: 100vh;
  background: var(--bg);
  padding: 30rpx 0 60rpx;
}
.head {
  text-align: center;
  margin-bottom: 44rpx;
  .title {
    display: block;
    font-size: 40rpx;
    font-weight: 700;
    color: var(--ink);
  }
  .sub {
    display: block;
    font-size: 24rpx;
    color: var(--ink-3);
    margin-top: 12rpx;
    line-height: 1.6;
    padding: 0 20rpx;
  }
}

.card {
  margin: 0 24rpx;
  background: var(--card);
  border-radius: var(--r-lg);
  padding: 44rpx 36rpx 40rpx;
  box-shadow: var(--shadow-card);
  position: relative;
}
.field {
  margin-bottom: 34rpx;
  &.center {
    text-align: center;
  }
  .label {
    display: block;
    font-size: 24rpx;
    font-weight: 500;
    color: var(--ink-2);
    margin-bottom: 18rpx;
    text-align: left;
  }
  .tip {
    display: block;
    font-size: 20rpx;
    color: var(--ink-4);
    margin-top: 14rpx;
  }
}

/* 头像 */
.avatar-btn {
  width: 168rpx;
  height: 168rpx;
  border-radius: 50%;
  padding: 0;
  margin: 0 auto;
  overflow: hidden;
  background: var(--brand-tint);
  border: 4rpx solid var(--brand);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8rpx 24rpx rgba(14, 158, 104, 0.2);
}
button.avatar-btn::after {
  border: none;
}
.avatar-ph-static {
  width: 168rpx;
  height: 168rpx;
  border-radius: 50%;
  margin: 0 auto;
  overflow: hidden;
  background: var(--brand-tint);
  border: 4rpx solid var(--brand);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8rpx 24rpx rgba(14, 158, 104, 0.2);
}
.avatar-img {
  width: 100%;
  height: 100%;
  border-radius: 50%;
}
.avatar-ph {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  .ph-plus {
    font-size: 64rpx;
    color: var(--brand);
    line-height: 1;
  }
}

/* 昵称 */
.nick-input {
  height: 100rpx;
  width: 100%;
  background: #f1f6f3;
  border: 1rpx solid #e3ece6;
  border-radius: var(--r-md);
  padding: 0 28rpx;
  font-size: 32rpx;
  color: var(--ink);
  box-sizing: border-box;
  text-align: center;
}
.ph {
  color: var(--ink-4);
  font-size: 28rpx;
}
.info-row {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
  background: #f5f9f6;
  border-radius: var(--r-sm);
  padding: 20rpx 24rpx;
  .info-item {
    font-size: 22rpx;
    color: var(--ink-3);
    line-height: 1.6;
  }
}

/* 主按钮 */
.btn {
  width: 100%;
  height: 100rpx;
  border-radius: 999rpx;
  background: var(--grad-brand);
  color: #fff;
  font-size: 32rpx;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-top: 10rpx;
  box-shadow: var(--shadow-btn);
  &.disabled {
    opacity: 0.45;
    box-shadow: none;
  }
  &.loading {
    opacity: 0.7;
  }
}
button.btn {
  line-height: 100rpx;
}
</style>
