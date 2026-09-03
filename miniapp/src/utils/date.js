export function today() {
  return fmt(new Date());
}

export function fmt(d) {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

export function addDays(dateStr, n) {
  const d = new Date(dateStr + "T00:00:00");
  d.setDate(d.getDate() + n);
  return fmt(d);
}

export function daysAgo(n) {
  return addDays(today(), -n);
}

export function monthOf(dateStr) {
  return dateStr.slice(0, 7);
}

export function weekdayCN(dateStr) {
  const d = new Date(dateStr + "T00:00:00");
  return "日一二三四五六"[d.getDay()];
}

export function niceDate(dateStr) {
  const t = today();
  if (dateStr === t) return "今天";
  if (dateStr === addDays(t, -1)) return "昨天";
  const [, m, d] = dateStr.split("-");
  return `${Number(m)}月${Number(d)}日`;
}
