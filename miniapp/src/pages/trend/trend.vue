<template>
  <view class="page">
    <!-- 范围切换 -->
    <view class="range-tabs">
      <view
        v-for="r in ranges"
        :key="r"
        class="range"
        :class="{ on: days === r }"
        @click="switchRange(r)"
      >
        <text class="range-num">{{ r }}</text>
        <text class="range-unit">天</text>
      </view>
    </view>

    <!-- 体重曲线 -->
    <view class="card">
      <view class="card-head">
        <view class="head-l">
          <text class="head-dot c-green" />
          <text class="card-title">体重趋势</text>
        </view>
        <view class="legend">
          <view class="lg"><text class="lg-line raw" /><text class="lg-txt">实测</text></view>
          <view class="lg"><text class="lg-line avg" /><text class="lg-txt">7日均线</text></view>
        </view>
      </view>

      <view class="canvas-wrap" v-if="points.length >= 2">
        <canvas
          id="trendChart"
          type="2d"
          class="trend-canvas"
          :style="{ height: '230px' }"
          @touchend="onTouchEnd"
        />
        <view class="axis">
          <text>{{ firstDate }}</text>
          <text>{{ lastDate }}</text>
        </view>
      </view>

      <view class="empty" v-else>
        <view class="empty-ico">📈</view>
        <text class="empty-text">还没有足够的体重记录</text>
        <text class="empty-sub">连续记录 3 天以上,这里就能看出趋势了</text>
      </view>

      <view class="metrics" v-if="points.length">
        <view class="metric">
          <text class="mv" :class="changeClass">{{ changeText }}</text>
          <text class="ml">区间变化 kg</text>
        </view>
        <view class="metric">
          <text class="mv">{{ rateText }}</text>
          <text class="ml">周均变化 kg</text>
        </view>
        <view class="metric">
          <text class="mv">{{ points.length }}</text>
          <text class="ml">记录天数</text>
        </view>
      </view>
    </view>

    <!-- 热量收支 -->
    <view class="card" v-if="calories.length">
      <view class="card-head">
        <view class="head-l">
          <text class="head-dot c-amber" />
          <text class="card-title">热量收支</text>
        </view>
        <view class="legend right">
          <view class="lg"><text class="lg-line bar-in" /><text class="lg-txt">摄入</text></view>
          <view class="lg"><text class="lg-line bar-out" /><text class="lg-txt">消耗</text></view>
        </view>
      </view>
      <view class="bars">
        <view class="bar-col" v-for="c in calories" :key="c.date">
          <view class="bar-stack">
            <view class="bar-in" :style="{ height: barHeight(c.intake) + 'rpx' }" />
            <view class="bar-out" :style="{ height: barHeight(c.burn) + 'rpx' }" />
          </view>
        </view>
      </view>
    </view>

    <!-- 本地规则分析 -->
    <view class="card" v-if="analysis">
      <view class="card-head">
        <view class="head-l">
          <text class="head-dot c-blue" />
          <text class="card-title">阶段分析</text>
        </view>
        <text class="source">{{ analysis.source }}</text>
      </view>

      <view class="score-row">
        <view class="score-wrap">
          <view class="score-ring">
            <view class="score-inner">
              <text class="score">{{ analysis.score }}</text>
            </view>
          </view>
          <text class="score-label">综合评分</text>
        </view>
        <view class="stage-box">
          <text class="stage-label">当前阶段</text>
          <text class="stage">{{ analysis.stage }}</text>
        </view>
      </view>

      <view class="block" v-if="analysis.risks.length">
        <text class="block-title">
          <text class="bt-ico warn">!</text>
          需要注意
        </text>
        <view class="item risk" v-for="(r, i) in analysis.risks" :key="i">{{ r }}</view>
      </view>

      <view class="block" v-if="analysis.tips.length">
        <text class="block-title">
          <text class="bt-ico good">✓</text>
          下一步建议
        </text>
        <view class="item tip" v-for="(t, i) in analysis.tips" :key="i">{{ t }}</view>
      </view>
    </view>

    <view class="disclaimer">数据仅供个人参考,不构成医疗建议</view>
  </view>
</template>

<script setup>
import { ref, computed, onMounted, getCurrentInstance, watch } from "vue";
import { statsApi } from "@/api";
import { useUserStore } from "@/store/user";
import uCharts from "@qiun/ucharts";

const user = useUserStore();
const ranges = [7, 30, 90];
const days = ref(30);

const points = ref([]);
const calories = ref([]);
const analysis = ref(null);

const firstDate = computed(() =>
  points.value.length ? points.value[0].date.slice(5) : ""
);
const lastDate = computed(() =>
  points.value.length ? points.value[points.value.length - 1].date.slice(5) : ""
);
const changeText = computed(() => {
  if (points.value.length < 2) return "--";
  const d =
    points.value[points.value.length - 1].weight - points.value[0].weight;
  return (d > 0 ? "+" : "") + d.toFixed(1);
});
const changeClass = computed(() => {
  const t = changeText.value;
;
  if (t === "--") return "";
  return Number(t) > 0 ? "up" : "down";
});
const rateText = computed(() => {
  const r = analysis.value?.metrics?.weekly_rate;
  if (r == null) return "--";
  return (Number(r) > 0 ? "+" : "") + Number(r).toFixed(2);
});

const maxCal = computed(() =>
  Math.max(100, ...calories.value.map((c) => Math.max(c.intake, c.burn)))
);
function barHeight(v) {
  return Math.round((v / maxCal.value) * 120);
}

function switchRange(r) {
  days.value = r;
  load();
}

// 图表数据
const chartCats = computed(() => points.value.map((p) => p.date.slice(5)));
const chartSeries = computed(() => [
  {
    name: "实测体重",
    data: points.value.map((p) => (p.weight == null ? null : Number(p.weight))),
  },
  {
    name: "7日均线",
    data: points.value.map((p) => (p.avg7 == null ? null : Number(p.avg7))),
  },
]);

// === uCharts 画布逻辑（从原 trend-chart 组件内联） ===
const instance = getCurrentInstance();
const dpr = uni.getSystemInfoSync().pixelRatio || 2;
let chart = null;
let ctx = null;
let canvasRect = null;
let widthPx = 0;
let heightPx = 230;
let initializing = false;

function computeRange() {
  const values = [];
  chartSeries.value.forEach((s) =>
    s.data.forEach((v) => {
      if (v != null && !Number.isNaN(Number(v))) values.push(Number(v));
    })
  );
  if (!values.length) return { min: 0, max: 10 };
  let min = Math.min(...values);
  let max = Math.max(...values);
  if (max - min < 1) {
    min -= 0.5;
    max += 0.5;
  }
  const pad = (max - min) * 0.15;
  return { min: +(min - pad).toFixed(1), max: +(max + pad).toFixed(1) };
}

function buildOpts() {
  const { min, max } = computeRange();
  return {
    type: "line",
    context: ctx,
    width: widthPx * dpr,
    height: heightPx * dpr,
    pixelRatio: dpr,
    categories: chartCats.value,
    series: chartSeries.value.map((s) => ({ name: s.name, data: s.data })),
    animation: true,
    background: "#FFFFFF",
    color: ["#c3d3ca", "#0E9E68"],
    padding: [14, 14, 4, 2],
    legend: { show: false },
    xAxis: {
      disableGrid: true,
      labelCount: 4,
      fontSize: 10,
      fontColor: "#8da698",
      axisLineColor: "#e4ede6",
    },
    yAxis: {
      gridType: "dash",
      dashLength: 4,
      gridColor: "#e4ede6",
      splitNumber: 4,
      min,
      max,
      fontSize: 10,
      fontColor: "#8da698",
      format: (v) => Number(v).toFixed(1),
    },
    extra: {
      lineChart: { type: "curve", width: 2.5, activeType: "hollow" },
      tooltip: {
        showArrow: false,
        border: true,
        borderWidth: 1,
        borderColor: "#0E9E68",
        bgColor: "#ffffff",
        fontColor: "#163c2f",
      },
    },
  };
}

function init() {
  if (initializing || !chartCats.value.length || !chartSeries.value.length) return;
  initializing = true;
  const q = uni.createSelectorQuery().in(instance.proxy);
  q.select("#trendChart").fields({ node: true, size: true });
  q.select("#trendChart").boundingClientRect();
  q.exec((res) => {
    initializing = false;
    const f = res && res[0];
    const rect = res && res[1];
    if (!f || !f.node) return;
    canvasRect = rect;
    widthPx = f.width;
    heightPx = f.height || 230;
    const node = f.node;
    node.width = widthPx * dpr;
    node.height = heightPx * dpr;
    ctx = node.getContext("2d");
    chart = new uCharts(buildOpts());
  });
}

function render() {
  if (!chartCats.value.length || !chartSeries.value.length) return;
  if (!ctx) {
    init();
    return;
  }
  ctx.clearRect(0, 0, widthPx * dpr, heightPx * dpr);
  chart = new uCharts(buildOpts());
}

function onTouchEnd(e) {
  if (!chart || !canvasRect) return;
  const t = (e.changedTouches || e.touches || [])[0];
  if (!t) return;
  try {
    chart.showToolTip(
      {
        x: (t.clientX - canvasRect.left) * dpr,
        y: (t.clientY - canvasRect.top) * dpr,
      },
      {
        format: (item, category) =>
          `${category} ${item.name} ${Number(item.data).toFixed(1)}`,
      }
    );
  } catch (err) {
    /* 坐标异常时静默忽略 */
  }
}
// === uCharts 内联结束 ===

async function load() {
  try {
    await user.ensureLogin();
    const [w, c, a] = await Promise.all([
      statsApi.weight(days.value),
      statsApi.calories(days.value),
      statsApi.analysis(days.value),
    ]);
    points.value = w?.points || [];
    calories.value = c || [];
    analysis.value = a;
  } catch (e) {
    console.error(e);
  }
}

onMounted(() => {
  load();
});

watch(() => [points.value], render);

defineExpose({ load });
</script>

<style scoped lang="scss">
.page {
  padding: 24rpx 0 40rpx;
}

/* 范围切换 */
.range-tabs {
  display: flex;
  margin: 0 24rpx;
  background: #fff;
  border-radius: 999rpx;
  padding: 10rpx;
  box-shadow: var(--shadow-card);
}
.range {
  flex: 1;
  display: flex;
  align-items: baseline;
  justify-content: center;
  padding: 18rpx 0;
  border-radius: 999rpx;
  color: var(--ink-3);
  transition: all 0.25s;
  &.on {
    background: var(--grad-brand);
    box-shadow: var(--shadow-btn);
  }
  .range-num {
    font-size: 32rpx;
    font-weight: 600;
  }
  .range-unit {
    font-size: 20rpx;
    margin-left: 4rpx;
  }
  &.on .range-num,
  &.on .range-unit {
    color: #fff;
  }
}

/* 卡片 */
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
  margin-bottom: 26rpx;
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
.legend {
  display: flex;
  &.right {
    .lg {
      margin-left: 0;
      margin-right: 20rpx;
      &:last-child {
        margin-right: 0;
      }
    }
  }
  .lg {
    display: flex;
    align-items: center;
    margin-left: 20rpx;
  }
  .lg-txt {
    font-size: 20rpx;
    color: var(--ink-3);
    margin-left: 8rpx;
  }
}
.lg-line {
  width: 26rpx;
  height: 6rpx;
  border-radius: 3rpx;
  &.raw {
    background: #c3d3ca;
  }
  &.avg {
    background: var(--grad-brand);
  }
  &.bar-in {
    background: var(--amber);
    width: 18rpx;
  }
  &.bar-out {
    background: var(--blue);
    width: 18rpx;
  }
}

/* 图表 */
.canvas-wrap {
  padding: 0 8rpx;
}
.trend-canvas {
  width: 100%;
  display: block;
}
.axis {
  display: flex;
  justify-content: space-between;
  font-size: 20rpx;
  color: var(--ink-4);
  padding: 8rpx 12rpx 0;
}
.empty {
  padding: 60rpx 0 40rpx;
  text-align: center;
  .empty-ico {
    font-size: 64rpx;
    margin-bottom: 20rpx;
  }
  .empty-text {
    display: block;
    font-size: 28rpx;
    font-weight: 500;
    color: var(--ink-2);
  }
  .empty-sub {
    display: block;
    font-size: 22rpx;
    color: var(--ink-4);
    margin-top: 10rpx;
  }
}

/* 指标 */
.metrics {
  display: flex;
  margin-top: 28rpx;
  padding-top: 26rpx;
  border-top: 1rpx solid var(--line);
}
.metric {
  flex: 1;
  text-align: center;
  &:not(:last-child) {
    border-right: 1rpx solid var(--line);
  }
  .mv {
    display: block;
    font-size: 36rpx;
    font-weight: 700;
    color: var(--ink);
    &.up {
      color: var(--red);
    }
    &.down {
      color: var(--brand-deep);
    }
  }
  .ml {
    display: block;
    font-size: 20rpx;
    color: var(--ink-3);
    margin-top: 8rpx;
  }
}

/* 热量柱状 */
.bars {
  display: flex;
  align-items: flex-end;
  height: 150rpx;
  gap: 6rpx;
  padding: 0 4rpx;
}
.bar-col {
  flex: 1;
  display: flex;
  justify-content: center;
}
.bar-stack {
  display: flex;
  align-items: flex-end;
  gap: 4rpx;
  width: 100%;
  justify-content: center;
}
.bar-in {
  width: 12rpx;
  background: linear-gradient(180deg, #f0b25c, #e5942c);
  border-radius: 6rpx 6rpx 0 0;
  min-height: 2rpx;
  transition: height 0.4s;
}
.bar-out {
  width: 12rpx;
  background: linear-gradient(180deg, #6cb1ee, #3d83c4);
  border-radius: 6rpx 6rpx 0 0;
  min-height: 2rpx;
  transition: height 0.4s;
}

/* 阶段分析 */
.source {
  font-size: 20rpx;
  color: var(--ink-3);
  background: #f1f6f3;
  padding: 8rpx 20rpx;
  border-radius: 999rpx;
}
.score-row {
  display: flex;
  align-items: center;
  margin-bottom: 10rpx;
}
.score-wrap {
  width: 240rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  flex-shrink: 0;
}
.score-ring {
  width: 170rpx;
  height: 170rpx;
  border-radius: 50%;
  background: conic-gradient(var(--brand) 0 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8rpx 24rpx rgba(14, 158, 104, 0.22);
}
.score-inner {
  width: 132rpx;
  height: 132rpx;
  border-radius: 50%;
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
}
.score {
  font-size: 56rpx;
  font-weight: 700;
  color: var(--brand-deep);
  line-height: 1;
}
.score-label {
  font-size: 22rpx;
  color: var(--ink-3);
  margin-top: 14rpx;
}
.stage-box {
  flex: 1;
  margin-left: 30rpx;
}
.stage-label {
  display: block;
  font-size: 22rpx;
  color: var(--ink-3);
  margin-bottom: 12rpx;
}
.stage {
  font-size: 32rpx;
  font-weight: 600;
  color: var(--ink);
  line-height: 1.6;
}
.block {
  margin-top: 26rpx;
  padding-top: 24rpx;
  border-top: 1rpx solid var(--line);
}
.block-title {
  display: flex;
  align-items: center;
  font-size: 26rpx;
  font-weight: 600;
  color: var(--ink-2);
  margin-bottom: 16rpx;
}
.bt-ico {
  width: 36rpx;
  height: 36rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22rpx;
  margin-right: 12rpx;
  &.warn {
    background: var(--amber-tint);
    color: #a86a10;
    font-weight: 700;
  }
  &.good {
    background: var(--brand-tint);
    color: var(--brand-deep);
    font-weight: 700;
  }
}
.item {
  font-size: 26rpx;
  line-height: 1.7;
  padding: 18rpx 24rpx;
  border-radius: var(--r-sm);
  margin-bottom: 12rpx;
}
.risk {
  background: var(--red-tint);
  color: #a23c33;
}
.tip {
  background: var(--brand-tint);
  color: #0b6e49;
}
.disclaimer {
  margin: 24rpx 32rpx 0;
  font-size: 20rpx;
  color: var(--ink-4);
  text-align: center;
}
</style>