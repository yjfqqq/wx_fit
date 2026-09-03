<template>
  <view class="page">
    <!-- ============ 分段切换 ============ -->
    <view class="tabs">
      <view
        v-for="(t, i) in tabs"
        :key="i"
        class="tab"
        :class="{ on: current === i }"
        @click="current = i"
      >
        <text>{{ t }}</text>
      </view>
    </view>

    <!-- 日期切换 -->
    <view class="date-bar">
      <view class="d-arrow" @click="shiftDay(-1)">
        <text class="chev">‹</text>
      </view>
      <view class="date-text">
        <text class="d-main">{{ dateText }}</text>
        <text class="d-sub">{{ dateFull }}</text>
      </view>
      <view class="d-arrow" :class="{ dim: isToday }" @click="shiftDay(1)">
        <text class="chev">›</text>
      </view>
    </view>

    <!-- ============ 体重 ============ -->
    <view v-show="current === 0" class="panel">
      <view class="card">
        <view class="card-head">
          <view class="head-l">
            <text class="head-dot c-green" />
            <text class="card-title">记录体重</text>
          </view>
          <text class="tip-inline">同一天重复记录会覆盖</text>
        </view>

        <view class="field big">
          <text class="label">体重（kg）</text>
          <view class="input-wrap">
            <input
              class="input big-input"
              type="digit"
              v-model="weightForm.weight_kg"
              placeholder="例如 65.5"
            />
            <text class="unit-suffix" v-if="weightForm.weight_kg">kg</text>
          </view>
        </view>

        <view class="field-row">
          <view class="field flex1">
            <text class="label">体脂率 %（选填）</text>
            <input class="input" type="digit" v-model="weightForm.body_fat" placeholder="--" />
          </view>
          <view class="field flex1">
            <text class="label">腰围 cm（选填）</text>
            <input class="input" type="digit" v-model="weightForm.waist_cm" placeholder="--" />
          </view>
        </view>

        <view class="field">
          <text class="label">备注（选填）</text>
          <input class="input" v-model="weightForm.note" placeholder="今天状态如何" />
        </view>

        <button class="btn" @click="saveWeight">保存体重</button>
      </view>

      <view class="card" v-if="weightList.length">
        <view class="card-head">
          <view class="head-l">
            <text class="head-dot c-green" />
            <text class="card-title">最近记录</text>
          </view>
        </view>
        <view class="row" v-for="w in weightList" :key="w.id">
          <view class="row-date">
            <text class="rd-main">{{ w.record_date.slice(5).replace("-", "/") }}</text>
            <text class="rd-sub">{{ w.record_date.slice(0, 4) }}</text>
          </view>
          <view class="row-main">
            <text class="rm-num">{{ w.weight_kg }}</text>
            <text class="rm-unit"> kg</text>
            <text class="chip blue" v-if="w.body_fat">体脂 {{ w.body_fat }}%</text>
          </view>
          <text class="del" @click="delWeight(w.id)">删除</text>
        </view>
      </view>
    </view>

    <!-- ============ 饮食 ============ -->
    <view v-show="current === 1" class="panel">
      <view class="card">
        <view class="card-head">
          <view class="head-l">
            <text class="head-dot c-amber" />
            <text class="card-title">记录饮食</text>
          </view>
        </view>

        <!-- 餐次 -->
        <view class="meal-tabs">
          <view
            v-for="m in mealTypes"
            :key="m.value"
            class="meal-tab"
            :class="{ on: mealForm.meal_type === m.value }"
            @click="mealForm.meal_type = m.value"
          >
            <text class="meal-ico" :class="'mt' + m.value">{{ m.short }}</text>
            <text class="meal-name">{{ m.label }}</text>
          </view>
        </view>

        <!-- 两种录入模式 -->
        <view class="mode-switch">
          <view
            class="mode"
            :class="{ on: mealMode === 'quick' }"
            @click="mealMode = 'quick'"
          >
            <text>⚡ 快速记录</text>
          </view>
          <view
            class="mode"
            :class="{ on: mealMode === 'search' }"
            @click="mealMode = 'search'"
          >
            <text>🔍 查食物库</text>
          </view>
        </view>

        <block v-if="mealMode === 'quick'">
          <view class="field">
            <text class="label">吃了什么</text>
            <input
              class="input"
              v-model="mealForm.title"
              placeholder="例如 午饭 麻辣烫"
            />
          </view>
          <text class="tip">不填热量也能记,先记下来最重要</text>
        </block>

        <block v-else>
          <view class="field">
            <text class="label">搜索食物</text>
            <input
              class="input"
              v-model="keyword"
              placeholder="名称或拼音首字母,如 jxr"
              @input="onSearch"
            />
          </view>

          <view class="food-list" v-if="foodResults.length">
            <view
              class="food-item"
              :class="{ picked: pickedFood && pickedFood.id === f.id && !f.is_custom === !pickedFood.is_custom }"
              v-for="f in foodResults"
              :key="(f.is_custom ? 'c' : 's') + f.id"
              @click="pickFood(f)"
            >
              <view class="food-main">
                <text class="food-name">{{ f.name }}</text>
                <text class="food-cat">{{ f.category }}</text>
              </view>
              <view class="food-kcal">
                <text class="fk-num">{{ f.calories_per_100g }}</text>
                <text class="fk-unit"> 千卡/100g</text>
              </view>
              <view class="food-check" v-if="pickedFood && pickedFood.id === f.id && !f.is_custom === !pickedFood.is_custom">✓</view>
            </view>
          </view>
          <text class="tip" v-else-if="keyword">
            没找到,可以
            <text class="link" @click="goCustom">自己加一个</text>
          </text>

          <view class="amount-box" v-if="pickedFood">
            <text class="amount-label">
              {{ pickedFood.name }} · 每份 {{ pickedFood.unit_weight_g }}g
            </text>
            <view class="amount-row">
              <input class="input amount-input" type="digit" v-model="amountInput" />
              <text class="amount-unit">{{ pickedFood.common_unit }}</text>
              <view class="amount-eq">
                <text class="ae-num">= {{ computedKcal }}</text>
                <text class="ae-unit"> 千卡</text>
              </view>
            </view>
          </view>
        </block>

        <button class="btn" @click="saveMeal">记录这一餐</button>
      </view>

      <view class="card" v-if="mealList.length">
        <view class="card-head">
          <view class="head-l">
            <text class="head-dot c-amber" />
            <text class="card-title">今天吃了</text>
          </view>
          <text class="sum-tag">{{ mealList.length }} 条</text>
        </view>
        <view class="row" v-for="m in mealList" :key="m.id">
          <view class="meal-badge" :class="'mt' + m.meal_type">
            <text>{{ mealLabel(m.meal_type) }}</text>
          </view>
          <text class="row-main">{{ m.title }}</text>
          <view class="row-kcal" v-if="m.calories != null">
            <text class="rk-num">{{ m.calories }}</text>
            <text class="rk-unit"> 千卡</text>
          </view>
          <text class="row-kcal none" v-else>未计热量</text>
          <text class="del" @click="delMeal(m.id)">删除</text>
        </view>
      </view>
    </view>

    <!-- ============ 运动 ============ -->
    <view v-show="current === 2" class="panel">
      <view class="card">
        <view class="card-head">
          <view class="head-l">
            <text class="head-dot c-blue" />
            <text class="card-title">记录运动</text>
          </view>
        </view>

        <view class="field">
          <text class="label">搜索运动</text>
          <input
            class="input"
            v-model="exKeyword"
            placeholder="如 跑步、跳绳、paobu"
            @input="onSearchExercise"
          />
        </view>

        <view class="chip-wrap" v-if="exResults.length">
          <view
            class="chip"
            :class="{ on: exForm.item_id === e.id }"
            v-for="e in exResults"
            :key="e.id"
            @click="pickExercise(e)"
          >
            <text>{{ e.name }}</text>
            <text class="chip-met" v-if="exForm.item_id === e.id">{{ e.met_value }} MET</text>
          </view>
        </view>

        <view class="field" v-if="exForm.item_id">
          <text class="label">时长（分钟）</text>
          <view class="input-wrap">
            <input class="input big-input" type="number" v-model="exForm.duration_min" />
            <text class="unit-suffix">min</text>
          </view>
          <view class="estimate" v-if="exEstimate">
            <text class="est-ico">🔥</text>
            <text class="est-main">预计消耗 {{ exEstimate }} 千卡</text>
            <text class="est-sub">按 MET {{ pickedMet }} 与你的体重估算</text>
          </view>
        </view>

        <block v-else>
          <view class="divider-line">
            <text class="dl-text">或手动填写</text>
          </view>
          <view class="field-row">
            <view class="field flex1">
              <text class="label">运动名称</text>
              <input class="input" v-model="exForm.name" placeholder="如 快走" />
            </view>
            <view class="field flex1">
              <text class="label">时长（分钟）</text>
              <input class="input" type="number" v-model="exForm.duration_min" placeholder="30" />
            </view>
          </view>
        </block>

        <view class="field">
          <text class="label">强度</text>
          <view class="intensity-row">
            <view
              v-for="s in intensities"
              :key="s.value"
              class="intensity"
              :class="{ on: exForm.intensity === s.value }"
              @click="exForm.intensity = s.value"
            >
              <view class="int-dot" :class="'i' + s.value" v-if="exForm.intensity === s.value" />
              <text>{{ s.label }}</text>
            </view>
          </view>
        </view>

        <button class="btn" @click="saveExercise">记录运动</button>
      </view>

      <view class="card" v-if="exList.length">
        <view class="card-head">
          <view class="head-l">
            <text class="head-dot c-blue" />
            <text class="card-title">今天的运动</text>
          </view>
          <text class="sum-tag">{{ exList.length }} 条</text>
        </view>
        <view class="row" v-for="e in exList" :key="e.id">
          <view class="ex-ico">🏃</view>
          <text class="row-main">{{ e.name }}</text>
          <view class="row-kcal" v-if="e.calories != null">
            <text class="rk-num">{{ e.calories }}</text>
            <text class="rk-unit"> 千卡</text>
          </view>
          <text class="row-dur">{{ e.duration_min }}min</text>
          <text class="del" @click="delExercise(e.id)">删除</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed } from "vue";
import { onShow } from "@dcloudio/uni-app";
import { foodApi, recordApi, statsApi } from "@/api";
import { useUserStore } from "@/store/user";
import { today, niceDate, addDays } from "@/utils/date";

const user = useUserStore();
const tabs = ["体重", "饮食", "运动"];
const current = ref(0);
const curDate = ref(today());

const isToday = computed(() => curDate.value === today());
const dateText = computed(() => niceDate(curDate.value));
const dateFull = computed(() => {
  const [y, m, d] = curDate.value.split("-");
  return `${y}年${Number(m)}月${Number(d)}日`;
});

function shiftDay(n) {
  const next = addDays(curDate.value, n);
  if (next > today()) return;
  curDate.value = next;
  loadDay();
}

// ---------------- 体重 ----------------
const weightForm = ref({ weight_kg: "", body_fat: "", waist_cm: "", note: "" });
const weightList = ref([]);

async function saveWeight() {
  const w = Number(weightForm.value.weight_kg);
  if (!w || w <= 0) return uni.showToast({ title: "请输入体重", icon: "none" });
  const payload = {
    record_date: curDate.value,
    weight_kg: w,
    note: weightForm.value.note || "",
  };
  if (weightForm.value.body_fat) payload.body_fat = Number(weightForm.value.body_fat);
  if (weightForm.value.waist_cm) payload.waist_cm = Number(weightForm.value.waist_cm);

  await recordApi.addWeight(payload);
  uni.showToast({ title: "已记录", icon: "success" });
  weightForm.value = { weight_kg: "", body_fat: "", waist_cm: "", note: "" };
  loadDay();
}

async function delWeight(id) {
  await recordApi.delWeight(id);
  loadDay();
}

// ---------------- 饮食 ----------------
const mealTypes = [
  { value: 1, label: "早餐", short: "早" },
  { value: 2, label: "午餐", short: "午" },
  { value: 3, label: "晚餐", short: "晚" },
  { value: 4, label: "加餐", short: "加" },
];
const mealMode = ref("quick");
const mealForm = ref({ meal_type: 2, title: "" });
const keyword = ref("");
const foodResults = ref([]);
const pickedFood = ref(null);
const amountInput = ref("1");
const mealList = ref([]);
let searchTimer = null;

const computedKcal = computed(() => {
  if (!pickedFood.value) return 0;
  const grams = Number(amountInput.value || 0) * Number(pickedFood.value.unit_weight_g);
  return Math.round((Number(pickedFood.value.calories_per_100g) * grams) / 100);
});

function onSearch() {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(async () => {
    if (!keyword.value.trim()) {
      foodResults.value = [];
      return;
    }
    try {
      const res = await foodApi.search({ keyword: keyword.value, size: 20 });
      foodResults.value = res.items || [];
    } catch (e) {
      foodResults.value = [];
    }
  }, 300);
}

function pickFood(f) {
  pickedFood.value = f;
  amountInput.value = "1";
}

async function saveMeal() {
  const payload = { record_date: curDate.value, meal_type: mealForm.value.meal_type };
  if (mealMode.value === "quick") {
    if (!mealForm.value.title.trim())
      return uni.showToast({ title: "写点什么吧", icon: "none" });
    payload.title = mealForm.value.title.trim();
  } else {
    if (!pickedFood.value) return uni.showToast({ title: "先选个食物", icon: "none" });
    payload.food_id = pickedFood.value.id;
    payload.amount_g =
      Number(amountInput.value || 0) * Number(pickedFood.value.unit_weight_g);
  }
  await recordApi.addMeal(payload);
  uni.showToast({ title: "已记录", icon: "success" });
  mealForm.value.title = "";
  pickedFood.value = null;
  keyword.value = "";
  foodResults.value = [];
  loadDay();
}

async function delMeal(id) {
  await recordApi.delMeal(id);
  loadDay();
}

function mealLabel(v) {
  const m = mealTypes.find((i) => i.value === v);
  return m ? m.label : "";
}

function goCustom() {
  uni.navigateTo({ url: "/pages/record/food-custom" });
}

// ---------------- 运动 ----------------
const exKeyword = ref("");
const exResults = ref([]);
const exList = ref([]);
const exForm = ref({ item_id: null, name: "", duration_min: 30, intensity: 2 });
const intensities = [
  { value: 1, label: "轻松" },
  { value: 2, label: "适中" },
  { value: 3, label: "吃力" },
];
const pickedMet = ref(null);
const exEstimate = ref(null);
let exTimer = null;

function onSearchExercise() {
  clearTimeout(exTimer);
  exTimer = setTimeout(async () => {
    try {
      const res = await foodApi.exercises({ keyword: exKeyword.value });
      exResults.value = res || [];
    } catch (e) {
      exResults.value = [];
    }
  }, 300);
}

function pickExercise(e) {
  exForm.value.item_id = e.id;
  exForm.value.name = e.name;
  pickedMet.value = e.met_value;
  calcEstimate();
}

async function calcEstimate() {
  if (!exForm.value.item_id || !exForm.value.duration_min) {
    exEstimate.value = null;
    return;
  }
  try {
    const s = await statsApi.summary(curDate.value);
    const w = s.weight_kg || 60;
    exEstimate.value = Math.round(
      (Number(pickedMet.value) * w * Number(exForm.value.duration_min)) / 60
    );
  } catch (e) {
    exEstimate.value = null;
  }
}

async function saveExercise() {
  const payload = {
    record_date: curDate.value,
    duration_min: Number(exForm.value.duration_min) || 0,
    intensity: exForm.value.intensity,
    name: exForm.value.name || "",
  };
  if (exForm.value.item_id) payload.item_id = exForm.value.item_id;
  if (!payload.name && !payload.item_id)
    return uni.showToast({ title: "选一个运动或填名称", icon: "none" });

  await recordApi.addExercise(payload);
  uni.showToast({ title: "已记录", icon: "success" });
  exForm.value = { item_id: null, name: "", duration_min: 30, intensity: 2 };
  exKeyword.value = "";
  exResults.value = [];
  exEstimate.value = null;
  loadDay();
}

async function delExercise(id) {
  await recordApi.delExercise(id);
  loadDay();
}

// ---------------- 载入 ----------------
async function loadDay() {
  try {
    await user.ensureLogin();
    const d = curDate.value;
    const [w, m, e] = await Promise.all([
      recordApi.listWeight({ start: addDays(d, -30), end: d }),
      recordApi.listMeal(d),
      recordApi.listExercise(d),
    ]);
    weightList.value = (w || []).slice().reverse().slice(0, 10);
    mealList.value = m || [];
    exList.value = e || [];
  } catch (err) {
    console.error(err);
  }
}

onShow(() => {
  const tab = uni.getStorageSync("record_tab");
  if (tab !== "") {
    current.value = Number(tab);
    uni.removeStorageSync("record_tab");
  }
  curDate.value = today();
  loadDay();
});
</script>

<style scoped lang="scss">
.page {
  padding: 24rpx 0 60rpx;
}

/* ============ 分段切换 ============ */
.tabs {
  display: flex;
  margin: 0 24rpx;
  background: #fff;
  border-radius: 999rpx;
  padding: 10rpx;
  box-shadow: var(--shadow-card);
}
.tab {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20rpx 0;
  font-size: 30rpx;
  font-weight: 500;
  color: var(--ink-3);
  border-radius: 999rpx;
  transition: all 0.25s;
  &.on {
    background: var(--grad-brand);
    color: #fff;
    font-weight: 600;
    box-shadow: var(--shadow-btn);
  }
}

/* ============ 日期条 ============ */
.date-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 28rpx 24rpx 8rpx;
}
.d-arrow {
  width: 72rpx;
  height: 72rpx;
  border-radius: 50%;
  background: #fff;
  box-shadow: var(--shadow-card);
  display: flex;
  align-items: center;
  justify-content: center;
  &.dim {
    opacity: 0.35;
  }
}
.chev {
  font-size: 44rpx;
  color: var(--brand-deep);
  line-height: 1;
  padding-bottom: 6rpx;
}
.date-text {
  min-width: 300rpx;
  text-align: center;
  padding: 0 30rpx;
  .d-main {
    display: block;
    font-size: 34rpx;
    font-weight: 600;
    color: var(--ink);
  }
  .d-sub {
    display: block;
    font-size: 22rpx;
    color: var(--ink-3);
    margin-top: 4rpx;
  }
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
  margin-bottom: 24rpx;
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
.tip-inline {
  font-size: 22rpx;
  color: var(--ink-4);
}
.sum-tag {
  font-size: 22rpx;
  color: var(--brand-deep);
  background: var(--brand-tint);
  padding: 6rpx 18rpx;
  border-radius: 999rpx;
}

/* ============ 表单 ============ */
.field {
  margin-bottom: 24rpx;
  &.big {
    margin-bottom: 28rpx;
  }
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
  height: 92rpx;
  width: 100%;
  background: #f1f6f3;
  border: 1rpx solid #e3ece6;
  border-radius: var(--r-md);
  padding: 0 26rpx;
  font-size: 30rpx;
  color: var(--ink);
  box-sizing: border-box;
}
.big-input {
  height: 112rpx;
  font-size: 52rpx;
  font-weight: 600;
}
.unit-suffix {
  position: absolute;
  right: 28rpx;
  top: 50%;
  transform: translateY(-50%);
  font-size: 28rpx;
  color: var(--ink-3);
  font-weight: 500;
}
.big-input ~ .unit-suffix {
  font-size: 32rpx;
}

/* ============ 主按钮 ============ */
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
  margin-top: 12rpx;
  box-shadow: var(--shadow-btn);
}
button.btn {
  line-height: 100rpx;
}
.hint {
  display: block;
  text-align: center;
  font-size: 22rpx;
  color: var(--ink-4);
  margin-top: 20rpx;
}

/* ============ 历史行 ============ */
.row {
  display: flex;
  align-items: center;
  padding: 24rpx 0;
  &:not(:last-child) {
    border-bottom: 1rpx solid var(--line);
  }
}
.row-date {
  width: 110rpx;
  flex-shrink: 0;
  .rd-main {
    display: block;
    font-size: 26rpx;
    font-weight: 600;
    color: var(--ink);
  }
  .rd-sub {
    display: block;
    font-size: 18rpx;
    color: var(--ink-4);
    margin-top: 2rpx;
  }
}
.row-main {
  font-size: 28rpx;
  color: var(--ink);
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.rm-num {
  font-size: 32rpx;
  font-weight: 600;
}
.rm-unit {
  font-size: 22rpx;
  color: var(--ink-3);
}
.chip {
  font-size: 18rpx;
  padding: 4rpx 12rpx;
  border-radius: 999rpx;
  margin-left: 14rpx;
  &.blue {
    color: #2c6ea8;
    background: var(--blue-tint);
  }
}
.del {
  font-size: 24rpx;
  color: var(--ink-4);
  padding: 8rpx 4rpx 8rpx 20rpx;
  flex-shrink: 0;
}
.row-kcal {
  text-align: right;
  flex-shrink: 0;
  margin-right: 10rpx;
  .rk-num {
    font-size: 28rpx;
    font-weight: 600;
    color: var(--brand-deep);
  }
  .rk-unit {
    font-size: 20rpx;
    color: var(--ink-3);
  }
  &.none {
    font-size: 20rpx;
    color: var(--amber);
  }
}
.row-dur {
  font-size: 20rpx;
  color: var(--ink-3);
  background: #f1f6f3;
  padding: 6rpx 14rpx;
  border-radius: 999rpx;
  margin-right: 6rpx;
  flex-shrink: 0;
}
.ex-ico {
  width: 60rpx;
  height: 60rpx;
  background: var(--blue-tint);
  border-radius: 18rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 30rpx;
  margin-right: 18rpx;
  flex-shrink: 0;
}

/* ============ 餐次选择 ============ */
.meal-tabs {
  display: flex;
  gap: 14rpx;
  margin-bottom: 24rpx;
}
.meal-tab {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 18rpx 0 16rpx;
  border-radius: var(--r-md);
  background: #f1f6f3;
  transition: all 0.2s;
  &.on {
    background: #fff;
    box-shadow: inset 0 0 0 2rpx var(--brand);
  }
  .meal-ico {
    width: 56rpx;
    height: 56rpx;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 26rpx;
    font-weight: 600;
    color: #fff;
    margin-bottom: 10rpx;
    &.mt1 {
      background: linear-gradient(135deg, #f2b04c, #e5942c);
    }
    &.mt2 {
      background: linear-gradient(135deg, #22bd85, #0d9a63);
    }
    &.mt3 {
      background: linear-gradient(135deg, #5da9e6, #3d83c4);
    }
    &.mt4 {
      background: linear-gradient(135deg, #a98bd8, #8a67c4);
    }
  }
  .meal-name {
    font-size: 22rpx;
    color: var(--ink-2);
  }
  &.on .meal-name {
    color: var(--brand-deep);
    font-weight: 600;
  }
}
.meal-badge {
  font-size: 20rpx;
  font-weight: 500;
  padding: 8rpx 18rpx;
  border-radius: 999rpx;
  margin-right: 18rpx;
  flex-shrink: 0;
  color: #fff;
  &.mt1 {
    background: linear-gradient(135deg, #f2b04c, #e5942c);
  }
  &.mt2 {
    background: linear-gradient(135deg, #22bd85, #0d9a63);
  }
  &.mt3 {
    background: linear-gradient(135deg, #5da9e6, #3d83c4);
  }
  &.mt4 {
    background: linear-gradient(135deg, #a98bd8, #8a67c4);
  }
}

/* ============ 模式切换 ============ */
.mode-switch {
  display: flex;
  background: #edf3ef;
  border-radius: 999rpx;
  padding: 8rpx;
  margin-bottom: 26rpx;
}
.mode {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 18rpx 0;
  font-size: 27rpx;
  color: var(--ink-3);
  border-radius: 999rpx;
  transition: all 0.2s;
  &.on {
    background: #fff;
    color: var(--brand-deep);
    font-weight: 600;
    box-shadow: 0 6rpx 16rpx rgba(20, 94, 62, 0.1);
  }
}
.tip {
  font-size: 22rpx;
  color: var(--ink-3);
  display: block;
  margin: -8rpx 0 22rpx;
}
.link {
  color: var(--brand-deep);
  font-weight: 500;
}

/* ============ 食物搜索结果 ============ */
.food-list {
  max-height: 460rpx;
  overflow-y: auto;
  margin-bottom: 22rpx;
}
.food-item {
  display: flex;
  align-items: center;
  padding: 22rpx 24rpx;
  border-radius: var(--r-md);
  background: #f5f9f6;
  margin-bottom: 12rpx;
  border: 1rpx solid transparent;
  &.picked {
    background: var(--brand-tint);
    border-color: var(--brand);
  }
}
.food-main {
  flex: 1;
  min-width: 0;
}
.food-name {
  display: block;
  font-size: 28rpx;
  font-weight: 500;
  color: var(--ink);
}
.food-cat {
  font-size: 20rpx;
  color: var(--ink-3);
  margin-top: 4rpx;
  display: block;
}
.food-kcal {
  flex-shrink: 0;
  .fk-num {
    font-size: 26rpx;
    font-weight: 600;
    color: var(--ink-2);
  }
  .fk-unit {
    font-size: 20rpx;
    color: var(--ink-3);
  }
}
.food-check {
  width: 40rpx;
  height: 40rpx;
  border-radius: 50%;
  background: var(--grad-brand);
  color: #fff;
  font-size: 24rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-left: 16rpx;
  flex-shrink: 0;
}
.amount-box {
  background: #f5f9f6;
  border-radius: var(--r-md);
  padding: 22rpx 24rpx;
  margin-bottom: 22rpx;
}
.amount-label {
  display: block;
  font-size: 22rpx;
  color: var(--ink-2);
  margin-bottom: 14rpx;
}
.amount-row {
  display: flex;
  align-items: center;
}
.amount-input {
  width: 200rpx;
  height: 84rpx;
  padding: 0 20rpx;
  font-size: 34rpx;
  font-weight: 600;
  background: #fff;
}
.amount-unit {
  font-size: 26rpx;
  color: var(--ink-2);
  margin-left: 16rpx;
}
.amount-eq {
  margin-left: auto;
  text-align: right;
  .ae-num {
    font-size: 32rpx;
    font-weight: 700;
    color: var(--brand-deep);
  }
  .ae-unit {
    font-size: 20rpx;
    color: var(--ink-3);
  }
}

/* ============ 运动 ============ */
.chip-wrap {
  display: flex;
  flex-wrap: wrap;
  gap: 14rpx;
  margin-bottom: 24rpx;
}
.chip {
  display: flex;
  align-items: center;
  padding: 16rpx 28rpx;
  background: #f1f6f3;
  border-radius: 999rpx;
  font-size: 26rpx;
  color: var(--ink-2);
  border: 1rpx solid transparent;
  &.on {
    background: var(--brand-tint);
    color: var(--brand-deep);
    border-color: var(--brand);
    font-weight: 600;
  }
}
.chip-met {
  font-size: 18rpx;
  color: var(--brand);
  margin-left: 10rpx;
  background: #fff;
  padding: 2rpx 12rpx;
  border-radius: 999rpx;
}
.estimate {
  display: flex;
  flex-direction: column;
  align-items: center;
  background: var(--brand-tint);
  border-radius: var(--r-md);
  padding: 24rpx;
  margin-top: 18rpx;
  .est-ico {
    font-size: 40rpx;
    margin-bottom: 8rpx;
  }
  .est-main {
    font-size: 30rpx;
    font-weight: 600;
    color: var(--brand-deep);
  }
  .est-sub {
    font-size: 20rpx;
    color: var(--ink-3);
    margin-top: 6rpx;
  }
}
.divider-line {
  display: flex;
  align-items: center;
  margin: 6rpx 0 24rpx;
  .dl-text {
    font-size: 22rpx;
    color: var(--ink-4);
    padding: 0 20rpx;
  }
  &::before,
  &::after {
    content: "";
    flex: 1;
    height: 1rpx;
    background: var(--line);
  }
}
.intensity-row {
  display: flex;
  gap: 14rpx;
}
.intensity {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20rpx 0;
  border-radius: var(--r-md);
  background: #f1f6f3;
  font-size: 26rpx;
  color: var(--ink-2);
  &.on {
    background: var(--brand-tint);
    color: var(--brand-deep);
    font-weight: 600;
  }
}
</style>
