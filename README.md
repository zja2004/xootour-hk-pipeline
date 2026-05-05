# XOOTOUR HK Restaurant Data Pipeline

🍜 **香港餐厅数据爬取管道** — 基于 TripAdvisor 公开 API + SSR 详情页的全量数据采集系统

## 📊 数据概况

### 数据文件

| 文件 | 来源 | 数量 | 大小 | 状态 |
|------|------|------|------|------|
| `hk_restaurants_api_list.json` | 公开 REST API | 10,000 | 5.65 MB | ✅ 完成 |
| `hk_restaurants_detail.json` | 详情页 SSR HTML | 9,951 | 8.53 MB | ✅ 完成 |
| **总计（合并后）** | — | **~10,000** | **~14 MB** | ✅ |

### API 列表数据字段

| 字段 | 完整率 | 说明 |
|------|--------|------|
| restaurantId | 100% | ⭐ 主键 |
| name | 100% | 餐厅中文名 |
| rating | 99.9% | 综合评分 0-5 |
| reviewCount | 99.8% | 点评数量 |
| price | 56.9% | 价格等级 ¥~¥¥¥¥ |
| cuisines | 96.0% | 菜系标签 |
| coverImage | 93.6% | 封面图 URL |
| detailPageUrl | 100% | 详情页链接 |

### 详情页补充字段

| 字段 | 完整率 | 说明 |
|------|--------|------|
| address | **100%** | 📍 中英文完整地址 |
| rankingString | **100%** | 🏆 排名如 "#1 / 13,750" |
| subratings | **86%** | 📊 食物/氛围/服务/性价比 |
| latitude/longitude | **79%** | 🗺️ GPS 坐标 |
| meals | **51%** | 🍽 餐时（午餐/晚餐等） |
| hours | **44%** | 🕐 营业时间段 |
| features | **38%** | ✨ 特色（Wifi/停车等） |
| awards | 1% | 🏅 旅行者之选等奖项 |
| phone | 0% | ⚠️ 需 Google Maps/OSM 补充 |
| website | 0% | ⚠️ 需 Google Maps/OSM 补充 |

**平均评分**: ⭐ 4.21/5

## 📁 项目结构

```
xootour-hk-pipeline/
├── README.md
├── FEASIBILITY_REPORT.md          # 平台可行性报告
├── TECHSTACK.md                   # 技术栈说明
├── data/
│   ├── raw/
│   │   ├── hk_restaurants_api_list.json    ⭐ 10,000家 API 数据
│   │   ├── hk_restaurants_detail.json      ⭐ 9,951家 详情页数据
│   │   └── detail_stats.json               统计数据
│   ├── processed/
│   │   └── hk_restaurants_v2.json           30家爬取测试
│   └── _deprecated/               # 旧 AI 假数据（保留参考）
└── scripts/
    ├── tripadvisor_scraper_v2.py   # 详情页单页爬虫
    ├── batch_api_crawler.py        # API 批量并发爬虫
    └── batch_detail_crawler.py     # 详情页批量并发爬虫
```

## 🚀 技术方案

### 阶段 1: API 列表抓取 ✅

通过 TripAdvisor 公开 API 批量获取全部 10,000 家餐厅基础信息。

```
端点: POST https://api.tripadvisor.cn/restapi/soa2/21218/restaurantListForPc
并发: 10 workers × 334 页
耗时: ~43 秒
```

### 阶段 2: 详情页批量爬取 ✅

利用 Next.js SSR 特性，从 HTML `__NEXT_DATA__` 直接提取数据，无需浏览器渲染。

```
方式: urllib GET 详情页 → 解析 <script id="__NEXT_DATA__">
并发: 20 workers × 10,000 页
耗时: ~7 分钟
成功率: 99.5% (9,951/10,000)
```

### 阶段 3: OpenStreetMap 补充 (进行中)

通过 Overpass API 匹配餐厅并提取电话、网站、营业时间。

```
端点: https://overpass-api.de/api/interpreter
策略: 批量查询 → 本地名称模糊匹配
```

## 🔍 数据样本

### Top 3 餐厅

**#1** Cruise 空中餐厅及酒吧 | ⭐4.9 (2,186评) | ¥¥ - ¥¥¥
> 📍 香港 北角村里1号 香港維港凱悅尚萃酒店西座23楼
> 📊 食物4.9/氛围4.7/服务4.9/性价比4.6

**#10** Pica Pica | ⭐4.8 (700评) | ¥¥ - ¥¥¥
> 📍 香港 上环德辅道中323号 启德商业大厦地下G-H铺
> 📊 食物4.8/氛围4.8/服务4.9/性价比4.6

**#94** Burger Joys | ⭐4.6 (388评) | ¥¥ - ¥¥¥
> 📍 香港 湾仔骆克道42-50号君悦居
> 📊 食物4.5/氛围4.2/服务4.4/性价比4.2

## 📋 待办事项

- [x] API 列表全量抓取 (10,000 家)
- [x] 详情页批量爬取 (9,951 家 → 地址/排名/子评分)
- [ ] OpenStreetMap 电话+网站补充
- [ ] 数据清洗与合并 (API + 详情页)
- [ ] 标准化输出 (JSON/CSV/数据库)
- [ ] 评论区数据提取管道

## 📄 许可

数据仅供研究学习使用，请遵守 TripAdvisor 服务条款。

## 🔗 相关链接

- TripAdvisor 香港: https://www.tripadvisor.cn/Restaurants-g294217-Hong_Kong.html
- XOOTOUR Spec V1: https://cuplore.com/view.php?file=XOO/XOOTOUR-RESTAURANT-SPEC-V1
- 本仓库: https://github.com/zja2004/xootour-hk-pipeline
