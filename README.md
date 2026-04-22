# 小A助手 · 厂商资源位监控日报

> 5 家厂商 × 72 个资源位 × 2 入口（应用商店 / 游戏中心）每日监控体系

## 🔗 在线 Demo

👉 **https://alextvt668.github.io/app-monitor-dashboard/**

> ⚠️ 当前页面为**演示数据**（mock），用于展示监控体系的结构与指标口径。
> 真机采集链路待设备 + 账号 + 固定 IP 到位后切换为实时数据。

## 📊 监控范围

| 厂商 | 应用商店 | 游戏中心 | 备注 |
|---|---|---|---|
| 华为 | ✅ | ✅ | EMUI + 纯血鸿蒙双设备 |
| OPPO | ✅ | ✅ | |
| vivo | ✅ | ✅ | |
| 小米 | ✅ | ✅ | |
| 荣耀 | ✅ | ✅ | |

## 🏗️ 架构

```
collector/  — 真机采集层（uiautomator2 / hdc + OCR）
parser/     — UI 树/OCR 结构化解析
storage/    — PostgreSQL + MinIO
scheduler/  — Celery beat 调度
analytics/  — 公司维度聚合 / Top 榜
pusher/     — 企微日报推送
dashboard/  — 前端可视化（当前托管页面）
api/        — FastAPI 查询接口
```

## 🧩 技术栈

- **采集**：uiautomator2（Android）/ hdc（HarmonyOS NEXT）+ Tesseract OCR
- **任务**：Celery + Redis + celery-beat（每日 02:00 跑批）
- **存储**：PostgreSQL（结构化） + MinIO（截图）
- **前端**：纯静态 HTML + ECharts 5.x
- **推送**：企微机器人 Webhook

## 📄 License

Internal use only.
