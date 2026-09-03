# 上线部署指南（从零到 HTTPS）

> 前提：一台云服务器 + 一个已备案域名。操作本身约 30 分钟（备案等待除外）。
> 架构：Docker Compose 一键起 **MySQL 8 + FastAPI 后端 + Caddy（自动 HTTPS）**。

## 0. 需要准备（花钱 / 等待的部分）

| 事项 | 说明 | 费用/耗时 |
|---|---|---|
| 服务器 | 阿里云/腾讯云轻量应用服务器 2核2G 起步够用，系统选 Ubuntu 22.04 | 新人价约 60-100 元/年 |
| 域名 | 任意 .com/.cn | 约 10-60 元/年 |
| ICP 备案 | 域名指向大陆服务器**必须备案**，小程序后台也要求域名已备案 | 7-20 天（云厂商控制台在线提交） |

## 1. DNS 解析（备案通过后）

域名控制台添加一条 **A 记录**：主机记录 `@`（或 `fit`），记录值 = 服务器公网 IP。

## 2. 服务器装 Docker

```bash
ssh root@服务器IP
curl -fsSL https://get.docker.com | bash
systemctl enable --now docker
```

## 3. 上传代码

本机执行（或用 git 仓库克隆）：

```bash
scp -r fit-app root@服务器IP:/opt/fit-app
```

## 4. 配置

```bash
cd /opt/fit-app/deploy
cp .env.production.example .env
vi .env          # 改 DB_PASSWORD / JWT_SECRET / WX_SECRET / WX_TEMPLATE_ID
vi Caddyfile     # 把 your-domain.com 换成你的域名
```

## 5. 启动

```bash
docker compose up -d --build
# 首次部署执行一次：建表 + 导入食物库/运动库种子数据
docker compose exec server python scripts/init_db.py
# 验证
curl http://127.0.0.1:8000/health
```

## 6. HTTPS（自动）

云控制台**安全组放行 80、443 端口**。Caddy 检测到域名解析正确后会
自动申请并续期 Let's Encrypt 证书，无需任何手动操作。

验证：浏览器打开 `https://你的域名/health`，应返回 `{"status":"ok",...}`。

## 7. 小程序端切换到线上

1. `miniapp/src/config.js` 的 `BASE_URL` 改为 `https://你的域名/api/v1`（文件里有三档说明）
2. 重新编译并上传体验版：`npm run build:mp-weixin` → 开发者工具上传
3. 小程序后台「开发管理 → 开发设置 → 服务器域名」：request 合法域名填 `https://你的域名`
4. 体验版全流程走一遍（登录/记录/趋势/提醒开关），没问题再提交审核

## 8. 数据备份（建议马上配）

```bash
mkdir -p /opt/backup
crontab -e   # 加一行，每天 3 点备份：
0 3 * * * docker exec fit-mysql sh -c 'mysqldump -uroot -p"$MYSQL_ROOT_PASSWORD" $MYSQL_DATABASE' | gzip > /opt/backup/fit_$(date +\%F).sql.gz
```

## 9. 提审注意（个人主体）

- 类目选「**工具**」，不要选医疗健康类
- 全部文案避免诊断/治疗/治愈等医疗表述（当前代码已规避，改文案时注意）
- 审核说明里写清功能路径：记录体重/饮食/运动 → 查看趋势，无需特殊权限
- 提醒功能用的是微信官方订阅消息，属合规能力，无需额外资质

## 常见问题

| 现象 | 排查 |
|---|---|
| `/health` 不通 | `docker compose ps` 看容器状态；`docker compose logs server` 看报错 |
| HTTPS 证书签发失败 | 域名解析未生效（`ping 域名`）、80 端口未放行 |
| 小程序请求失败 | request 合法域名是否已配；BASE_URL 是否 https；备案是否完成 |
| 登录报 40029 | 体验版/正式版的 code 需要真实登录链路，确认 `WX_MOCK_LOGIN=false` 且 WX_SECRET 正确 |
| 提醒收不到 | `WX_TEMPLATE_ID` 是否配置；用户是否点过订阅授权；`docker compose logs server` 看 21:05 的任务日志 |
