<template>
  <view class="page">
    <!-- 范围切换（紧凑药丸，不再独占一行的大卡片） -->
    <view class="range-row">
      <view class="rangepill" role="tablist" aria-label="体重趋势时间范围">
        <view
          v-for="r in ranges"
          :key="r"
          class="rangepill-item hit"
          :class="{ on: days === r }"
          role="tab"
          :aria-selected="days === r"
          @click="switchRange(r)"
        >
          <text class="num">{{ r }}</text>
          <text class="rp-unit">天</text>
        </view>
      </view>
    </view>

    <!-- 体重曲线 -->
    <view class="card">
      <view class="card-head">
        <view class="head-l">
          <text class="head-dot c-green" />
          <text class="card-title">体重趋势</text>
        </view>
        <text class="p-meta">近 {{ days }} 天</text>
      </view>

      <view class="canvas-wrap" v-if="points.length >= 2">
        <canvas
          id="trendChart"
          type="2d"
          class="trend-canvas"
          :style="{ height: '230px' }"
          role="img"
          :aria-label="'体重趋势折线图，展示近 ' + days + ' 天体重变化'"
          @touchend="onTouchEnd"
        />
        <view class="axis">
          <text class="num">{{ firstDate }}</text>
          <text class="num">{{ lastDate }}</text>
        </view>
      </view>

      <view class="empty" v-else>
        <view class="empty-ico">📈</view>
        <text class="empty-text">还没有足够的体重记录</text>
        <text class="empty-sub">连续记录 3 天以上,这里就能看出趋势了</text>
      </view>

      <!-- 图例移到图表下方：375px 宽下标题 + 两个图例必然挤压 -->
      <view class="legend below">
        <view class="lg"><text class="lg-line raw" /><text class="lg-txt">实测</text></view>
        <view class="lg"><text class="lg-line avg" /><text class="lg-txt">7日均线</text></view>
      </view>

      <view class="metrics" v-if="points.length">
        <view class="metric">
          <text class="mv num" :class="changeClass">{{ changeText }}</text>
          <text class="ml">区间变化 kg</text>
        </view>
        <view class="metric">
          <text class="mv num">{{ rateText }}</text>
          <text class="ml">周均变化 kg</text>
        </view>
        <view class="metric">
          <text class="mv num">{{ points.length }}</text>
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
        <text class="p-meta">近 {{ days }} 天</text>
      </view>

      <view class="bars-wrap">
        <view class="bars-axis">
          <text class="by num">{{ maxCal }}</text>
          <text class="by num">0</text>
        </view>
        <view class="bars-inner">
          <view
            class="budget-line"
            v-if="budgetBottomPct !== null"
            :style="{ bottom: budgetBottomPct + '%' }"
          >
            <text class="bl-val num">预算 {{ budget }}</text>
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
      </view>
      <view class="legend below">
        <view class="lg"><text class="lg-line bar-in" /><text class="lg-txt">摄入</text></view>
        <view class="lg"><text class="lg-line bar-out" /><text class="lg-txt">消耗</text></view>
        <view class="lg" v-if="budget"><text class="lg-line bl" /><text class="lg-txt">预算</text></view>
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
import { ref, computed, getCurrentInstance, watch, nextTick } from "vue";
import { onShow } from "@dcloudio/uni-app";
import { statsApi } from "@/api";
import { useUserStore } from "@/store/user";
import { today } from "@/utils/date";
import { applyTheme, theme } from "@/utils/theme";
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

const maxCal = computed(() => {
  // 用所有天 intake/burn 的最大值做基准；若全 0 给一个保底 800 让柱子有合理高度
  const vals = calories.value.flatMap((c) => [Number(c?.intake) || 0, Number(c?.burn) || 0]);
  const m = vals.length ? Math.max(...vals) : 0;
  return m > 0 ? m : 800;
});
// v >= 0 时按比例算高度，最小给 6rpx 让有数据的柱子可见；v == 0 时直接给 0（避免全是底部细线）
function barHeight(v) {
  const n = Number(v) || 0;
  if (n <= 0) return 0;
  return Math.max(6, Math.round((n / maxCal.value) * 120));
}

// 每日热量预算：用于柱状图上的虚线基线，没有设预算时不画
const budget = ref(null);
const budgetBottomPct = computed(() => {
  if (!budget.value) return null;
  const p = (Number(budget.value) / maxCal.value) * 100;
  if (!Number.isFinite(p) || p <= 0 || p >= 100) return null;
  return p;
});

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
  // 主题感知：深色模式下把图表字面量配色切到暗色板（canvas 不支持 CSS 变量）
  const dark = theme.value === "dark";
  const c = {
    bg: dark ? "#16211C" : "#FFFFFF",
    axis: dark ? "#87998F" : "#5A7568",
    line: dark ? "#26352E" : "#E1E8E4",
    brand: dark ? "#4ECB8B" : "#06794C",
    ink: dark ? "#E8EFEA" : "#0F2419",
    track: dark ? "#34453C" : "#CBD6CF",
  };
  return {
    type: "line",
    context: ctx,
    width: widthPx * dpr,
    height: heightPx * dpr,
    pixelRatio: dpr,
    categories: chartCats.value,
    series: chartSeries.value.map((s) => ({ name: s.name, data: s.data })),
    animation: true,
    background: c.bg,
    color: [c.track, c.brand],
    padding: [14, 14, 4, 2],
    legend: { show: false },
    xAxis: {
      disableGrid: true,
      labelCount: 4,
      fontSize: 10,
      fontColor: c.axis,
      axisLineColor: c.line,
    },
    yAxis: {
      gridType: "dash",
      dashLength: 4,
      gridColor: c.line,
      splitNumber: 4,
      min,
      max,
      fontSize: 10,
      fontColor: c.axis,
      format: (v) => Number(v).toFixed(1),
    },
    extra: {
      lineChart: { type: "curve", width: 2.5, activeType: "hollow" },
      tooltip: {
        showArrow: false,
        border: true,
        borderWidth: 1,
        borderColor: c.brand,
        bgColor: c.bg,
        fontColor: c.ink,
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
    const [w, c, a, s] = await Promise.all([
      statsApi.weight(days.value),
      statsApi.calories(days.value),
      statsApi.analysis(days.value),
      statsApi.summary(today()),
    ]);
    points.value = w?.points || [];
    calories.value = c || [];
    analysis.value = a;
    budget.value = s?.budget_kcal != null ? Number(s.budget_kcal) : null;
  } catch (e) {
    console.error(e);
  }
}

onShow(() => {
  load();
  applyTheme();
});

watch(() => [points.value], () => {
  nextTick(render);
});

// 主题切换时重绘图表（canvas 用字面量配色，需主动重建）
watch(theme, () => {
  if (chart) render();
});

defineExpose({ load });
</script>

<style scoped lang="scss">
.page {
  padding: 24rpx 0 40rpx;
}

/* 范围切换（紧凑药丸，靠 ::after 把热区补到 88rpx） */
.range-row {
  display: flex;
  justify-content: flex-end;
  padding: 8rpx var(--pad-x) 0;
}
.rangepill {
  display: flex;
  background: var(--surface-2);
  border-radius: var(--r-pill);
  padding: 6rpx;
}
.rangepill-item {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 60rpx;
  padding: 0 24rpx;
  border-radius: var(--r-pill);
  color: var(--ink-3);
  position: relative;
  transition: all var(--d-fast) var(--e-out);
  &::after { content: ""; position: absolute; inset: -12rpx 0; }
  &.on {
    background: var(--card);
    box-shadow: var(--shadow-card);
  }
  .num {
    font-size: 28rpx;
    line-height: 1;
  }
  .rp-unit {
    font-size: 20rpx;
    line-height: 1;
    margin-left: 4rpx;
  }
  &.on text {
    color: var(--brand);
    font-weight: 700;
  }
}

/* 卡片 */
.card {
  background: var(--card);
  border: 1rpx solid var(--line);
  border-radius: var(--r-lg);
  padding: var(--pad-card);
  margin: var(--gap-card) var(--pad-x) 0;
  box-shadow: var(--shadow-card);
  overflow: hidden;
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
  min-width: 0;
}
.head-dot {
  width: 12rpx;
  height: 12rpx;
  border-radius: 50%;
  margin-right: 16rpx;
  flex-shrink: 0;
  &.c-green { background: var(--brand); }
  &.c-amber { background: var(--amber-fill); }
  &.c-blue  { background: var(--blue-fill); }
}
.card-title {
  font-size: 32rpx;
  font-weight: 600;
  color: var(--ink);
  letter-spacing: -0.4rpx;
}
.p-meta {
  font-size: 21rpx;
  color: var(--ink-3);
  flex-shrink: 0;
  font-variant-numeric: tabular-nums;
}
.legend {
  display: flex;
  justify-content: center;
  gap: 32rpx;
  &.below {
    margin-top: 20rpx;
    padding-top: 20rpx;
    border-top: 1rpx solid var(--line);
  }
  .lg {
    display: flex;
    align-items: center;
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
    background: var(--line-strong);
  }
  &.avg {
    background: var(--grad-brand);
  }
  &.bl {
    background: repeating-linear-gradient(90deg, var(--ink-3) 0 6rpx, transparent 6rpx 12rpx);
    height: 2rpx;
    width: 30rpx;
  }
  &.bar-in {
    background: var(--brand);
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
  color: var(--ink-3);
  padding: 8rpx 12rpx 0;
}
.empty {
  padding: 64rpx 0 40rpx;
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
    color: var(--ink-3);
    margin-top: 8rpx;
  }
}

/* 指标 */
.metrics {
  display: flex;
  margin-top: 24rpx;
  padding-top: 24rpx;
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

/* 热量柱状：加了 y 轴刻度与预算虚线基线，否则读不出绝对值 */
.bars-wrap {
  display: flex;
  gap: 12rpx;
}
.bars-axis {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  height: 180rpx;
  flex-shrink: 0;
  .by {
    font-size: 18rpx;
    color: var(--ink-3);
    line-height: 1;
    transform: translateY(-4rpx);
    &:last-child { transform: translateY(4rpx); }
  }
}
.bars-inner {
  flex: 1;
  min-width: 0;
  position: relative;
}
.budget-line {
  position: absolute;
  left: 0;
  right: 0;
  height: 0;
  border-top: 2rpx dashed var(--amber-fill);
  z-index: 2;
  .bl-val {
    position: absolute;
    right: 0;
    top: -32rpx;
    font-size: 18rpx;
    font-weight: 700;
    color: var(--amber);
    background: var(--card);
    padding: 0 6rpx;
    line-height: 1.4;
  }
}
.bars {
  display: flex;
  align-items: flex-end;
  height: 180rpx;
  gap: 4rpx;
  padding: 8rpx 4rpx 12rpx;
  overflow: hidden;
  box-sizing: border-box;
}
.bar-col {
  flex: 1;
  display: flex;
  justify-content: center;
  height: 100%;
  align-items: flex-end;
  min-width: 0;
}
.bar-stack {
  display: flex;
  align-items: flex-end;
  gap: 4rpx;
  width: 100%;
  justify-content: center;
  height: 100%;
}
.bar-in {
  width: 12rpx;
  background: var(--brand);
  border-radius: 6rpx 6rpx 0 0;
  box-sizing: border-box;
}
.bar-out {
  width: 12rpx;
  background: var(--blue-fill);
  border-radius: 6rpx 6rpx 0 0;
  box-sizing: border-box;
}

/* 阶段分析 */
.source {
  font-size: 20rpx;
  color: var(--ink-3);
  background: var(--surface-2);
  padding: 8rpx 20rpx;
  border-radius: var(--r-pill);
}
.score-row {
  display: flex;
  align-items: center;
  margin-bottom: 8rpx;
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
  box-shadow: var(--shadow-btn);
}
.score-inner {
  width: 132rpx;
  height: 132rpx;
  border-radius: 50%;
  background: var(--card);
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
  margin-top: 12rpx;
}
.stage-box {
  flex: 1;
  margin-left: 32rpx;
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
  margin-top: 24rpx;
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
    color: var(--amber);
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
  padding: 16rpx 24rpx;
  border-radius: var(--r-sm);
  margin-bottom: 12rpx;
}
.risk {
  background: var(--red-tint);
  color: var(--red);
}
.tip {
  background: var(--brand-tint);
  color: var(--brand);
}
.disclaimer {
  margin: 24rpx 32rpx 0;
  font-size: 20rpx;
  color: var(--ink-3);
  text-align: center;
}
</style>