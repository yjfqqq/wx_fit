<template>
  <view class="page">
    <view class="card">
      <view class="card-head">
        <view class="head-l">
          <text class="head-dot c-amber" />
          <text class="card-title">新增自定义食物</text>
        </view>
      </view>
      <text class="sub">用于记录食物库里没有的菜,数值按每 100g 填</text>

      <view class="field">
        <text class="label">名称</text>
        <input class="input" v-model="form.name" placeholder="例如 妈妈做的红烧排骨" />
      </view>

      <view class="field-row">
        <view class="field flex1">
          <text class="label">热量（千卡/100g）</text>
          <input class="input" type="digit" v-model="form.calories_per_100g" placeholder="0" />
        </view>
        <view class="field flex1">
          <text class="label">每份克重（g）</text>
          <input class="input" type="digit" v-model="form.unit_weight_g" placeholder="100" />
        </view>
      </view>

      <view class="macro-head">
        <text class="label macro-l">三大营养素（每 100g）</text>
        <text class="macro-tip">选填,填了趋势页更准确</text>
      </view>
      <view class="macro-row">
        <view class="macro-item">
          <view class="macro-dot p" />
          <text class="macro-name">蛋白质</text>
          <input class="input mini" type="digit" v-model="form.protein" placeholder="0" />
          <text class="macro-unit">g</text>
        </view>
        <view class="macro-item">
          <view class="macro-dot c" />
          <text class="macro-name">碳水</text>
          <input class="input mini" type="digit" v-model="form.carbs" placeholder="0" />
          <text class="macro-unit">g</text>
        </view>
        <view class="macro-item">
          <view class="macro-dot f" />
          <text class="macro-name">脂肪</text>
          <input class="input mini" type="digit" v-model="form.fat" placeholder="0" />
          <text class="macro-unit">g</text>
        </view>
      </view>

      <view class="field">
        <text class="label">份量单位</text>
        <input class="input" v-model="form.common_unit" placeholder="份" />
      </view>

      <button class="btn" @click="save">保存</button>
      <text class="hint">只填热量也能用,三大营养素可以留空</text>
    </view>

    <view class="card" v-if="list.length">
      <view class="card-head">
        <view class="head-l">
          <text class="head-dot c-green" />
          <text class="card-title">我的自定义食物</text>
        </view>
        <text class="count-tag">{{ list.length }} 个</text>
      </view>
      <view class="row" v-for="f in list" :key="f.id">
        <view class="row-ico">🍲</view>
        <view class="row-main">
          <text class="fname">{{ f.name }}</text>
          <text class="fsub">
            {{ f.calories_per_100g }} 千卡/100g · 1{{ f.common_unit }} = {{ f.unit_weight_g }}g
          </text>
        </view>
        <text class="del" @click="remove(f.id)">删除</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref } from "vue";
import { onShow } from "@dcloudio/uni-app";
import { foodApi } from "@/api";
import { useUserStore } from "@/store/user";
import { applyTheme } from "@/utils/theme";

const user = useUserStore();
const list = ref([]);
const form = ref({
  name: "",
  calories_per_100g: "",
  protein: "0",
  fat: "0",
  carbs: "0",
  common_unit: "份",
  unit_weight_g: "100",
});

async function save() {
  if (!form.value.name.trim()) {
    return uni.showToast({ title: "填个名字吧", icon: "none" });
  }
  const payload = {
    name: form.value.name.trim(),
    calories_per_100g: Number(form.value.calories_per_100g) || 0,
    protein: Number(form.value.protein) || 0,
    fat: Number(form.value.fat) || 0,
    carbs: Number(form.value.carbs) || 0,
    common_unit: form.value.common_unit || "份",
    unit_weight_g: Number(form.value.unit_weight_g) || 100,
  };
  await foodApi.addCustom(payload);
  uni.showToast({ title: "已添加", icon: "success" });
  form.value = {
    name: "",
    calories_per_100g: "",
    protein: "0",
    fat: "0",
    carbs: "0",
    common_unit: "份",
    unit_weight_g: "100",
  };
  load();
}

async function remove(id) {
  await foodApi.delCustom(id);
  load();
}

async function load() {
  try {
    await user.ensureLogin();
    list.value = await foodApi.listCustom();
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
.page {
  padding: 24rpx 0 64rpx;
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
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8rpx;
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
  &.c-amber {
    background: var(--amber);
  }
  &.c-green {
    background: var(--brand);
  }
}
.card-title {
  font-size: 32rpx;
  font-weight: 600;
  color: var(--ink);
}
.sub {
  display: block;
  font-size: 22rpx;
  color: var(--ink-3);
  margin: 8rpx 0 24rpx;
}
.count-tag {
  font-size: 22rpx;
  color: var(--brand-deep);
  background: var(--brand-tint);
  padding: 6rpx 16rpx;
  border-radius: var(--r-pill);
}

.field {
  margin-bottom: 24rpx;
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

/* 三大营养素 */
.macro-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 12rpx;
  .label {
    margin-bottom: 0;
  }
  .macro-tip {
    font-size: 20rpx;
    color: var(--ink-3);
  }
}
.macro-row {
  display: flex;
  gap: 16rpx;
  margin-bottom: 24rpx;
}
.macro-item {
  flex: 1;
  position: relative;
  background: var(--surface-2);
  border-radius: var(--r-md);
  padding: 16rpx 16rpx 12rpx;
  .macro-dot {
    width: 12rpx;
    height: 12rpx;
    border-radius: 50%;
    margin-bottom: 8rpx;
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
  .macro-name {
    display: block;
    font-size: 20rpx;
    color: var(--ink-3);
    margin-bottom: 8rpx;
  }
}
.input.mini {
  height: 64rpx;
  padding: 0 16rpx;
  font-size: 28rpx;
  font-weight: 500;
  padding-right: 40rpx;
  background: var(--card);
}
.macro-unit {
  position: absolute;
  right: 24rpx;
  bottom: 32rpx;
  font-size: 20rpx;
  color: var(--ink-3);
  pointer-events: none;
}

.btn {
  width: 100%;
  height: 100rpx;
  border-radius: var(--r-pill);
  background: var(--grad-brand);
  color: var(--on-brand);
  font-size: 32rpx;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-top: 8rpx;
  box-shadow: var(--shadow-btn);
}
button.btn {
  line-height: 100rpx;
}
.hint {
  display: block;
  text-align: center;
  font-size: 22rpx;
  color: var(--ink-3);
  margin-top: 20rpx;
}

/* 我的自定义食物 */
.row {
  display: flex;
  align-items: center;
  padding: 24rpx 0;
  &:not(:last-child) {
    border-bottom: 1rpx solid var(--line);
  }
}
.row-ico {
  width: 68rpx;
  height: 68rpx;
  border-radius: 20rpx;
  background: var(--amber-tint);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32rpx;
  margin-right: 20rpx;
  flex-shrink: 0;
}
.row-main {
  flex: 1;
  min-width: 0;
}
.fname {
  display: block;
  font-size: 28rpx;
  font-weight: 500;
  color: var(--ink);
}
.fsub {
  display: block;
  font-size: 20rpx;
  color: var(--ink-3);
  margin-top: 6rpx;
}
.del {
  font-size: 24rpx;
  color: var(--red);
  padding: 8rpx 4rpx 8rpx 20rpx;
  flex-shrink: 0;
}
</style>
