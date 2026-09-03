<template>
  <view class="page">
    <view class="card">
      <view class="card-head">
        <view class="head-l">
          <text class="head-dot c-green" />
          <text class="card-title">设置减重目标</text>
        </view>
      </view>

      <view class="field-row">
        <view class="field flex1">
          <text class="label">起始体重（kg）</text>
          <view class="input-wrap">
            <input class="input" type="digit" v-model="form.start_weight" placeholder="80" />
            <text class="unit-suffix" v-if="form.start_weight">kg</text>
          </view>
        </view>
        <view class="field flex1">
          <text class="label">目标体重（kg）</text>
          <view class="input-wrap">
            <input class="input" type="digit" v-model="form.target_weight" placeholder="70" />
            <text class="unit-suffix" v-if="form.target_weight">kg</text>
          </view>
        </view>
      </view>

      <view class="field">
        <text class="label">目标日期（选填）</text>
        <picker mode="date" :value="form.target_date" :start="todayStr" @change="onDate">
          <view class="picker" :class="{ empty: !form.target_date }">
            {{ form.target_date || "不设期限" }}
            <text class="chev-r">›</text>
          </view>
        </picker>
      </view>

      <view class="field">
        <view class="deficit-head">
          <text class="label">每日热量缺口</text>
          <text class="deficit-val">{{ form.daily_deficit }}<text class="dv-unit"> 千卡</text></text>
        </view>
        <slider
          :value="form.daily_deficit"
          min="0"
          max="1000"
          step="50"
          activeColor="#0e9e68"
          backgroundColor="#e4ede6"
          block-size="26"
          block-color="#ffffff"
          @changing="onDeficit"
        />
        <view class="slider-hint">
          <text>0 · 维持</text>
          <text>500 ≈ 每周减 0.5kg</text>
          <text>1000 · 激进</text>
        </view>
      </view>

      <button class="btn" @click="save">保存目标</button>
      <view class="note">
        <text class="note-ico">💡</text>
        <text>
          每天 500 千卡缺口对应每周约减 0.5kg,是比较可持续的节奏。
          设置过大缺口容易反弹,后端也会把摄入限制在不低于基础代谢。
        </text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { authApi } from "@/api";
import { useUserStore } from "@/store/user";
import { today } from "@/utils/date";

const user = useUserStore();
const todayStr = today(); // 本地时区的今天（toISOString 是 UTC，凌晨会差一天）
const form = ref({
  start_weight: "",
  target_weight: "",
  target_date: "",
  daily_deficit: 500,
});

function onDate(e) {
  form.value.target_date = e.detail.value;
}
function onDeficit(e) {
  form.value.daily_deficit = e.detail.value;
}

async function save() {
  const payload = { daily_deficit: Number(form.value.daily_deficit) };
  if (form.value.start_weight) payload.start_weight = Number(form.value.start_weight);
  if (form.value.target_weight) payload.target_weight = Number(form.value.target_weight);
  if (form.value.target_date) payload.target_date = form.value.target_date;

  await user.saveGoal(payload);
  uni.showToast({ title: "已保存", icon: "success" });
  setTimeout(() => uni.navigateBack(), 600);
}

onMounted(async () => {
  try {
    await user.ensureLogin();
    const g = await authApi.getGoal();
    if (g) {
      form.value = {
        start_weight: g.start_weight ? String(g.start_weight) : "",
        target_weight: g.target_weight ? String(g.target_weight) : "",
        target_date: g.target_date || "",
        daily_deficit: g.daily_deficit || 500,
      };
    }
  } catch (e) {
    console.error(e);
  }
});
</script>

<style scoped lang="scss">
.page {
  padding: 24rpx 0 60rpx;
  background: var(--bg);
  min-height: 100vh;
}
.card {
  background: var(--card);
  border-radius: var(--r-lg);
  padding: 32rpx;
  margin: 24rpx;
  box-shadow: var(--shadow-card);
}
.card-head {
  display: flex;
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
  background: var(--brand);
}
.card-title {
  font-size: 32rpx;
  font-weight: 600;
  color: var(--ink);
}

.field {
  margin-bottom: 30rpx;
}
.field-row {
  display: flex;
  gap: 20rpx;
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
.input-wrap {
  position: relative;
}
.input {
  height: 100rpx;
  width: 100%;
  background: #f1f6f3;
  border: 1rpx solid #e3ece6;
  border-radius: var(--r-md);
  padding: 0 26rpx;
  font-size: 34rpx;
  font-weight: 500;
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
.picker {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 100rpx;
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

/* 缺口滑杆 */
.deficit-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  .label {
    margin-bottom: 0;
  }
  .deficit-val {
    font-size: 36rpx;
    font-weight: 700;
    color: var(--brand-deep);
    .dv-unit {
      font-size: 22rpx;
      font-weight: 400;
      color: var(--ink-3);
    }
  }
}
.slider-hint {
  display: flex;
  justify-content: space-between;
  font-size: 20rpx;
  color: var(--ink-4);
  margin-top: 4rpx;
}

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
  margin-top: 16rpx;
  box-shadow: var(--shadow-btn);
}
button.btn {
  line-height: 100rpx;
}
.note {
  display: flex;
  align-items: flex-start;
  margin-top: 26rpx;
  background: #f5f9f6;
  border-radius: var(--r-sm);
  padding: 20rpx 24rpx;
  font-size: 22rpx;
  color: var(--ink-3);
  line-height: 1.7;
  .note-ico {
    margin-right: 12rpx;
  }
}
</style>
