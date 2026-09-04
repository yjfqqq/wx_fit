<template>
  <view class="page">
    <view class="goal-overview card">
      <view class="goal-item"><view class="goal-circle"><text>{{ form.start_weight || "--" }}</text></view><text>起始 kg</text></view>
      <view class="goal-flow"><text class="flow-arrow">→</text><text class="flow-tag">{{ form.daily_deficit }} 千卡/日</text></view>
      <view class="goal-item"><view class="goal-circle target"><text>{{ form.target_weight || "--" }}</text></view><text>目标 kg</text></view>
    </view>

    <view class="card">
      <view class="card-head"><view class="head-l"><text class="head-dot c-amber" /><text class="card-title">目标设置</text></view></view>
      <view class="field">
        <text class="label">目标体重（kg）</text>
        <view class="input-wrap"><input class="input input-big" type="digit" inputmode="decimal" v-model="form.target_weight" placeholder="例如 62.0" /><text class="unit-suffix" v-if="form.target_weight">kg</text></view>
      </view>
      <view class="field">
        <text class="label">每日热量缺口</text>
        <view class="seg" role="radiogroup" aria-label="每日热量缺口">
          <view v-for="item in deficitOptions" :key="item.value" class="seg-item" :class="{ on: form.daily_deficit === item.value }" role="radio" :aria-checked="form.daily_deficit === item.value" @click="form.daily_deficit = item.value">{{ item.label }}</view>
        </view>
        <text class="field-help">{{ deficitHelp }}</text>
      </view>
      <view class="field last-field">
        <text class="label">目标日期（选填）</text>
        <picker mode="date" :value="form.target_date" :start="todayStr" @change="onDate"><view class="picker" :class="{ empty: !form.target_date }">{{ form.target_date || "不设期限" }}<text>›</text></view></picker>
      </view>
    </view>

    <view class="card">
      <view class="card-head"><view class="head-l"><text class="head-dot c-blue" /><text class="card-title">身体数据</text></view></view>
      <view class="field-row">
        <view class="field flex1"><text class="label">起始体重（kg）</text><view class="input-wrap"><input class="input" type="digit" inputmode="decimal" v-model="form.start_weight" placeholder="例如 68.0" /><text class="unit-suffix" v-if="form.start_weight">kg</text></view></view>
        <view class="field flex1"><text class="label">当前体重（kg）</text><view class="current-weight">以最新体重记录为准</view></view>
      </view>
    </view>

    <view class="tip"><text>💡</text><text>缺口越大掉得越快，但也越难坚持。300 千卡/日通常是更容易长期坚持的节奏。</text></view>
    <view class="save-area"><button class="btn btn-primary" @click="save">保存目标</button><text>目标可随时修改，改动只影响之后的测算</text></view>
  </view>
</template>

<script setup>
import { computed, ref, onMounted } from "vue";
import { onShow } from "@dcloudio/uni-app";
import { authApi } from "@/api";
import { useUserStore } from "@/store/user";
import { today } from "@/utils/date";
import { applyTheme } from "@/utils/theme";

const user = useUserStore();
const todayStr = today();
const deficitOptions = [{ value: 200, label: "200" }, { value: 300, label: "300" }, { value: 500, label: "500" }];
const form = ref({ start_weight: "", target_weight: "", target_date: "", daily_deficit: 300 });
const deficitHelp = computed(() => form.value.daily_deficit === 200 ? "稳一点：进度较慢，但对日常影响更小。" : form.value.daily_deficit === 500 ? "快一点：需要更稳定的饮食和运动配合。" : "推荐：约每周 0.3 kg，兼顾速度与可持续性。 ");
function onDate(e) { form.value.target_date = e.detail.value; }
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
      const deficit = Number(g.daily_deficit);
      form.value = { start_weight: g.start_weight ? String(g.start_weight) : "", target_weight: g.target_weight ? String(g.target_weight) : "", target_date: g.target_date || "", daily_deficit: [200, 300, 500].includes(deficit) ? deficit : 300 };
    }
  } catch (e) { console.error(e); }
});
onShow(() => applyTheme());
</script>

<style scoped lang="scss">
.page { min-height: 100vh; padding: var(--gap-card) 0 48rpx; background: var(--bg); }
.card { margin: 0 var(--pad-x) var(--gap-card); }
.goal-overview { display: flex; align-items: center; justify-content: space-between; padding: 36rpx var(--pad-card); }
.goal-item { display: flex; flex-direction: column; align-items: center; gap: 12rpx; color: var(--ink-3); font-size: 22rpx; }
.goal-circle { width: 112rpx; height: 112rpx; border-radius: 50%; display: flex; align-items: center; justify-content: center; background: var(--surface-2); border: 1rpx solid var(--line); color: var(--ink); font-size: 34rpx; font-weight: 700; }.goal-circle.target { background: var(--brand-tint); border-color: var(--brand); color: var(--brand); }
.goal-flow { flex: 1; min-width: 0; display: flex; flex-direction: column; align-items: center; gap: 8rpx; color: var(--ink-3); }.flow-arrow { font-size: 34rpx; line-height: 1; }.flow-tag { padding: 5rpx 14rpx; background: var(--amber-tint); border-radius: var(--r-pill); color: var(--amber); font-size: 20rpx; font-weight: 600; white-space: nowrap; }
.field { margin-bottom: var(--gap-field); }.last-field { margin-bottom: 0; }.label { display: block; margin-bottom: var(--gap-label); color: var(--ink-2); font-size: 25rpx; font-weight: 600; }.input-wrap { position: relative; }.input { background: var(--card); }.input-big { font-size: 44rpx; min-height: 112rpx; }.picker { min-height: var(--hit-min); padding: 0 24rpx; display: flex; align-items: center; justify-content: space-between; border: 1rpx solid var(--line-strong); border-radius: var(--r-md); color: var(--ink); background: var(--card); font-size: 28rpx; }.picker.empty { color: var(--ink-3); }.field-help { display: block; margin-top: 14rpx; color: var(--ink-3); font-size: 22rpx; line-height: 1.6; }.field-row { display: flex; gap: var(--gap-field); }.flex1 { flex: 1; min-width: 0; }.current-weight { min-height: var(--hit-min); display: flex; align-items: center; padding: 0 20rpx; border: 1rpx solid var(--line); border-radius: var(--r-md); background: var(--surface-2); color: var(--ink-3); font-size: 22rpx; white-space: nowrap; }
.tip { display: flex; gap: 12rpx; margin: 0 var(--pad-x) 32rpx; padding: 20rpx 24rpx; border-radius: var(--r-md); background: var(--amber-tint); color: var(--ink-2); font-size: 23rpx; line-height: 1.65; }.save-area { margin: 0 var(--pad-x); text-align: center; }.save-area text { display: block; margin-top: 16rpx; color: var(--ink-3); font-size: 21rpx; }.btn { width: 100%; }
</style>
