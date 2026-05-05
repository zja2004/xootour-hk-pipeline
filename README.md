# XOOTOUR HK Restaurant Data Pipeline

TripAdvisor 香港餐厅数据采集管道 — 10,000 家餐厅结构化数据。

## 数据集

| 文件 | 大小 | 说明 |
|------|------|------|
| `data/raw/hk_restaurants_10k_merged.json` | 9.5MB | ★ 主要数据集：10K 餐厅 API+详情合并 |
| `data/raw/hk_restaurants_api_raw.json` | 5.8MB | TripAdvisor API 原始响应 |
| `data/raw/hk_restaurants_detail_raw.json` | 8.5MB | 详情页爬虫原始数据 |
| `data/raw/hk_osm_enriched.json` | 830KB | OSM 地图数据匹配结果 |

## 字段覆盖（10K 餐厅）

| 字段 | 覆盖率 | 来源 |
|------|--------|------|
| restaurantId, name | 100% | API |
| rating | 99.9% | API |
| reviewCount | 100% | API |
| cuisines (菜系) | 96.0% | 详情页 |
| address (地址) | 99.5% | 详情页 |
| ranking (排名) | 100% | API |
| hours (营业时间) | 43.6% | 详情页 |
| subratings (分项评分) | 85.3% | 详情页 |
| price (价格等级) | 56.9% | API |
| features (特色) | 37.6% | 详情页 |

> ⚠️ phone/website/email 当前为 0%（详情页 JS 渲染问题，待修复）

## 技术栈

- **数据源**: TripAdvisor (API + 详情页)
- **爬虫**: Python + Playwright
- **数据格式**: JSON

## 更新日志

- 2026-05-05: 10K 餐厅数据上传（API + 详情页合并）
