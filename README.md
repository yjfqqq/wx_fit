# 减肥记录小程序（fit-app）

> uni-app (Vue3) + FastAPI + MySQL ｜ 微信静默登录 ｜ 活力青绿「治愈自然」UI
> 设计规范(v2):`docs/ui-design-v2.html`(六屏高保真 + Design Tokens)| 旧清爽风设计稿:`../docs/ui-design.html` ｜ 计划文档:`../docs/PLAN.md`

## 项目结构

```
fit-app/
├── server/          FastAPI 后端
│   ├── app/
│   │   ├── api/v1/        接口层（auth/records/foods/summary/stats）
│   │   ├── core/          配置、数据库、JWT、鉴权依赖
│   │   ├── models/        SQLAlchemy 模型（10 张表）
│   │   ├── schemas/       Pydantic 请求/响应模型
│   │   ├── services/      calc（BMR/TDEE/MET 算法）、wechat、summary 重算
│   │   └── db/seed_data.py  预置食物 150+ / 运动 53 条
│   ├── scripts/
│   │   ├── init_db.py     建库建表 + 导入种子数据
│   │   └── smoke_test.py  端到端冒烟测试（14 项）
│   ├── requirements.txt
│   └── .env.example
└── miniapp/         uni-app 前端（Vue3 + Vite）
    └── src/
        ├── pages/           index / record / trend / profile + goal、food-custom
        ├── api/             request.js（自动带 token、401 重登）+ 接口封装
        └── store/           Pinia 用户状态
```

## 后端启动

```bash
cd server

# 1. 建虚拟环境并安装依赖（只做一次）
python -m venv venv
venv\Scripts\pip install -r requirements.txt

# 2. 配置环境变量
copy .env.example .env
#   没装 MySQL：改 .env 里 DB_ENGINE=sqlite，可立即体验
#   装了 MySQL：保持 DB_ENGINE=mysql，填 DB_PASSWORD

# 3. 初始化数据库（建表 + 导入食物库/运动库）
venv\Scripts\python scripts\init_db.py

# 4. 启动
venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
```

打开 http://127.0.0.1:8000/docs 可看到全部 26 个接口的交互式文档。
跑 `scripts/smoke_test.py` 可一键验证 14 项端到端流程（需先启动服务）。

## 前端启动

推荐用 **HBuilderX**：新建 uni-app Vue3 项目（或 `npx degit dcloudio/uni-preset-vue#vite`），
把 `miniapp/src/` 内容覆盖进去，运行到微信开发者工具。

命令行方式：

```bash
cd miniapp
npm install
npm run dev:mp-weixin
# 用微信开发者工具打开 dist/dev/mp-weixin
```

**后端地址**在 `miniapp/src/config.js` 里切换（三档：开发者工具模拟器 / 真机预览局域网 IP / 正式域名），改完重新编译。

**微信开发者工具**：详情 → 本地设置 → 勾选「不校验合法域名」（本地调试必须）。

## 上线部署

见 [`deploy/DEPLOY.md`](deploy/DEPLOY.md)：Docker Compose 一键起 MySQL + 后端 + Caddy 自动 HTTPS，
含备案、DNS、备份、提审注意事项的完整 runbook。

## 关键配置（server/.env）

| 配置 | 说明 |
|---|---|
| `DB_ENGINE` | `mysql`（正式）或 `sqlite`（本机无 MySQL 时体验用） |
| `WX_MOCK_LOGIN` | `true`：不需要 AppID/AppSecret 即可跑通全部业务（返回固定 openid） |
| `WX_APPID` / `WX_SECRET` | 小程序后台拿到后填入，并把上面开关改为 `false` |

## 已实现

- 微信静默登录 + JWT 鉴权（正式 AppID 与 mock 模式可切换，切换方法见下表）
- 体重 / 饮食 / 运动三类记录的增删查，写入自动重算每日汇总
- 饮食双通道：快速记录（只写一句话）与查库记录（自动带热量）
- 食物库 150+ 条（支持拼音首字母搜索 jxr→鸡胸肉）、运动库 53 条（MET 估算消耗）
- 自定义食物
- 每日总览 / 月历打卡 / 体重趋势（7 日均线，uCharts 平滑曲线 + 点击查看数值）/ 热量收支 / 总体概览
- BMR（Mifflin-St Jeor）/ TDEE / 热量预算（安全下限保护）/ BMI 中国标准
- 本地规则分析：评分、阶段判断、风险提醒、建议（无 AI 成本）
- 数据导出 CSV（「我的」页入口，带 BOM 防 Excel 乱码）
- 趋势页 uCharts 图表（@qiun/ucharts，canvas 2d 高分屏适配，点击查看数值）
- TabBar 图标素材（4 枚 Lucide 线性图标，81×81 PNG 灰/绿两态，路径 `miniapp/src/static/tabbar/`；生成脚本 `miniapp/scripts/gen_tabbar_icons.py`，从 Iconify 取 SVG 后由 sharp 栅格化成 PNG，改色或换图标直接重跑脚本）
- 每日体重打卡提醒（微信订阅消息）：「我的」页开启 → 每天定时推送给当天还没记体重的用户。
  需在小程序后台申领模板，把模板 ID 填到 `server/.env` 的 `WX_TEMPLATE_ID` 后重启后端生效；
  定时任务在 `WX_REMIND_HOUR`（默认 21 点）触发，模板字段映射见 `app/services/wx_message.py`

## 待办（对应 PLAN.md M3-M4）

- [ ] 上线部署（需备案域名 + HTTPS，见 PLAN.md 第十一节）
