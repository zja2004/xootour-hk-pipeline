# XOOTOUR HK Restaurant Data Pipeline

TripAdvisor 香港餐厅数据采集管道 — 10,000 家餐厅结构化数据。

## 📊 数据集

| 文件 | 大小 | 说明 |
|------|------|------|
| `data/raw/hk_restaurants_v2.json` | — | ★ 主要数据集：API+详情合并（推荐） |
| `data/raw/hk_restaurants_api_list.json` | 5.8MB | TripAdvisor API 10K 原始响应 |
| `data/raw/hk_restaurants_detail.json` | 8.5MB | 详情页爬虫 9,951 条原始数据 |
| `data/raw/detail_stats.json` | — | 字段覆盖率统计 |
| `data/_deprecated/` | — | V1 旧数据（30条） |

## 📈 字段覆盖（10K 餐厅）

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
| meals (餐食类型) | 50.8% | 详情页 |
| features (特色) | 37.6% | 详情页 |

> ⚠️ **phone / website / email 当前为 0%**（详情页 JS 动态渲染，Playwright 爬虫未成功提取 — 待修复）

## 🎯 与 Spec V2 的映射

见 [XOOTOUR-RESTAURANT-SPEC-V2](https://www.cuplore.com/view.php?file=XOO/XOOTOUR-RESTAURANT-SPEC-V2)

| Spec 层 | 已有覆盖率 | 缺口 |
|---------|-----------|------|
| L1 基础信息 | ~80% | name_en/zh 分离、district 提取、contact_phone 0% |
| L2 消费能力 | ~60% | 人均消费金额缺失、支付方式缺失 |
| L3 外宾友好 | ~10% | 英文菜单、多语言支持等未采集 |
| L4 内容AI | ~30% | AI 标签、照片库未建立 |
| L5 质量血源 | 0% | 需新增：采集时间戳、置信度、多源验证 |

## 🔧 技术栈

- **数据源**: TripAdvisor (API + 详情页 Playwright)
- **爬虫**: `scripts/tripadvisor_scraper_v2.py`, `scripts/batch_detail_crawler.py`
- **输出**: JSON

## 📝 更新日志

- 2026-05-05: 10K 数据上传，README 更新 spec 映射
- 2026-05-03: 9,951 详情页 + 10K API 合并
- 2026-04-28: V2 pipeline 初始提交（30 条测试）
