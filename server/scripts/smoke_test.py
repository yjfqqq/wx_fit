"""端到端冒烟测试：登录 → 写资料 → 设目标 → 记三类记录 → 读汇总与统计。

用法（后端已启动）：
    python scripts/smoke_test.py
"""

import json
import urllib.error
import urllib.request
from urllib.parse import quote

ROOT = "http://127.0.0.1:8000"
BASE = ROOT + "/api/v1"


def call(method, path, data=None, token=None):
    url = path if path.startswith("http") else BASE + path
    req = urllib.request.Request(
        url,
        method=method,
        data=json.dumps(data).encode() if data is not None else None,
        headers={
            "Content-Type": "application/json",
            **({"Authorization": f"Bearer {token}"} if token else {}),
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, json.loads(r.read() or b"null")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"null")


def show(title, status, body):
    ok = "PASS" if 200 <= status < 300 else "FAIL"
    print(f"[{ok}] {title} ({status})")
    print("     ", json.dumps(body, ensure_ascii=False)[:220])
    return 200 <= status < 300


def main():
    today = "2026-09-03"
    results = []

    results.append(show("健康检查", *call("GET", ROOT + "/health")))

    # 真实登录模式下假 code 会失败，自动降级用 DEBUG 测试登录
    s, login = call("POST", "/auth/login", {"code": "mock", "nickname": "测试用户"})
    if 200 <= s < 300:
        results.append(show("微信登录（mock 模式）", s, login))
    else:
        s, login = call("POST", "/auth/test-login")
        results.append(show("微信登录（降级为 DEBUG 测试登录）", s, login))
    if not (200 <= s < 300):
        print("登录失败，无法继续后续测试（请检查 .env 或启动 DEBUG 模式）")
        raise SystemExit(1)
    token = login["token"]

    s, _ = call(
        "PUT",
        "/auth/profile",
        {
            "gender": 1,
            "birthday": "1995-06-15",
            "height_cm": 175,
            "activity_level": 2,
        },
        token,
    )
    results.append(show("填写身体资料", s, call("GET", "/auth/me", token=token)[1]))

    s, goal = call(
        "PUT",
        "/auth/goal",
        {"start_weight": 80, "target_weight": 70, "daily_deficit": 500},
        token,
    )
    results.append(show("设置目标", s, goal))

    s, w = call(
        "POST",
        "/records/weight",
        {"weight_kg": 78.5, "record_date": today, "body_fat": 22.5},
        token,
    )
    results.append(show("记录体重", s, w))

    s, foods = call("GET", "/foods?keyword=jxr", token=token)
    results.append(show("搜索食物（拼音首字母 jxr）", s, foods))
    food_id = foods["items"][0]["id"] if foods.get("items") else None

    if food_id:
        s, meal = call(
            "POST",
            "/records/meal",
            {
                "record_date": today,
                "meal_type": 2,
                "food_id": food_id,
                "amount_g": 150,
            },
            token,
        )
        results.append(show("记录饮食（查库带出热量）", s, meal))

    s, meal2 = call(
        "POST",
        "/records/meal",
        {"record_date": today, "meal_type": 2, "title": "同事请的奶茶"},
        token,
    )
    results.append(show("记录饮食（快速记录，无热量）", s, meal2))

    s, exs = call("GET", "/exercises?keyword=" + quote("跑步"), token=token)
    ex_id = exs[0]["id"] if exs else None
    if ex_id:
        s, ex = call(
            "POST",
            "/records/exercise",
            {"record_date": today, "item_id": ex_id, "duration_min": 30},
            token,
        )
        results.append(show("记录运动（MET 估算消耗）", s, ex))

    results.append(show("今日总览", *call("GET", f"/summary?date={today}", token=token)))
    results.append(show("热量预算测算", *call("GET", "/stats/plan", token=token)))
    results.append(show("体重趋势", *call("GET", "/stats/weight?days=30", token=token)))
    results.append(show("本地规则分析", *call("GET", "/stats/analysis?days=30", token=token)))
    results.append(show("月历打卡", *call("GET", "/summary/calendar?month=2026-09", token=token)))

    passed = sum(1 for r in results if r)
    total = len(results)
    print(f"\n===== {passed}/{total} 项通过 =====")
    if passed < total:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
