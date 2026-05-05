# XOOTOUR HK Restaurant Data Pipeline

🍜 **香港餐厅数据爬取管道** — 基于 TripAdvisor 公开 API 的批量数据采集系统

## 📊 数据概况

| 指标 | 数值 |
|------|------|
| 平台 | TripAdvisor.cn (猫途鹰) |
| 地区 | 香港 (geoId=294217) |
| 餐厅总数 | **10,000 家** |
| 数据来源 | 公开 REST API (api.tripadvisor.cn) |
| 采集方式 | 并发分页请求 (334页 × 30条) |
| 采集耗时 | ~43 秒 |
| 数据大小 | 5.65 MB (JSON) |

## 📁 项目结构

```
xootour-hk-pipeline/
├── README.md                     # 本文件
├── FEASIBILITY_REPORT.md         # 平台可行性报告
├── TECHSTACK.md                  # 技术栈说明
├── data/
│   ├── raw/                      # 原始爬取数据
│   │   ├── hk_restaurants_api_list.json  ⭐ 10,000家餐厅 API 数据
│   │   └── ... (历史数据文件)
│   └── processed/                # 清洗后数据
│       └── hk_restaurants_v2.json      30家详情页爬取测试
└── scripts/                      # 爬虫脚本
    └── tripadvisor_scraper_v2.py # 详情页单页爬虫
```

## 🗂️ API 数据结构 (hk_restaurants_api_list.json)

```json
{
  "source": "tripadvisor_api",
  "geoId": 294217,
  "location": "香港",
  "total": 10000,
  "restaurants": [
    {
      "restaurantId": "14982719",
      "locationId": 294217,
      "name": "Cruise 空中餐厅及酒吧",
      "rating": "4.9",
      "reviewCount": 2186,
      "price": "¥¥ - ¥¥¥",
      "cuisines": ["酒吧餐", "亚洲料理", "餐吧", "多国料理", "餐厅"],
      "coverImage": "https://...",
      "status": "正在营业",
      "reviews": ["All you can eat Tuesday", "Very good"],
      "awards": []
    }
  ]
}
```

### 字段说明

| 字段 | 说明 | 完整度 |
|------|------|--------|
| `restaurantId` | TripAdvisor 餐厅唯一 ID | 100% |
| `name` | 餐厅名称 | 100% |
| `rating` | 综合评分 (0-5) | 99.9% |
| `reviewCount` | 点评数量 | 99.8% |
| `price` | 价格等级 (¥~¥¥¥¥) | 56.9% |
| `cuisines` | 菜系标签 | 96.0% |
| `coverImage` | 封面图 URL | 93.6% |
| `status` | 营业状态 | ~90% |
| `reviews` | 点评片段 (2条) | ~80% |
| `awards` | 奖项 (e.g. 旅行者之选) | ~15% |

## 🔍 API vs 详情页数据对比

| 数据项 | API 数据 | 详情页 | 备注 |
|--------|----------|--------|------|
| 名称 | ✅ | ✅ | 一致 |
| 评分 | ✅ | ✅ | 一致 |
| 点评数 | ✅ | ✅ | 一致 |
| 价格 | ✅ | ✅ | 一致 |
| 菜系 | ✅ | ✅ | API 更全(含泛类标签) |
| 排名 | ❌ | ✅ | e.g. #1/13,750 |
| **地址** | ❌ | ✅ | 中英文完整地址 |
| 营业时间 | ❌ | ✅ | 餐时(午餐/晚餐/早午餐等) |
| 子评分 | ❌ | ✅ | 食物/氛围/服务/性价比 |
| 电话 | ❌ | ⚠️ | 仅已认领店铺 |
| 网站 | ❌ | ⚠️ | 仅已认领店铺 |
| 完整评论 | ❌ (仅片段) | ✅ | 含评分分布/语言分布 |
| 照片数 | ❌ | ✅ | 全部照片计数 |

**结论**: API 数据已覆盖所有核心字段(名称/评分/价格/菜系)，详情页主要提供 **地址**、**排名**、**子评分**、**完整评论** 四个关键增量字段。

## 🚀 快速开始

### 1. 批量获取餐厅列表

```python
import requests, json

url = "https://api.tripadvisor.cn/restapi/soa2/21218/restaurantListForPc"
headers = {"Content-Type": "application/json", "User-Agent": "TripAdvisor/1.0"}

# Token 从 TripAdvisor 首页 __NEXT_DATA__ 中获取
payload = {
    "filters": [],
    "currentPage": 1,
    "pageSize": 30,
    "sort": "default",
    "sourceType": "pc",
    "strategy": "default",
    "token": "YOUR_TOKEN_HERE"
}

resp = requests.post(url, json=payload, headers=headers)
data = resp.json()  # 返回 30 家餐厅
```

### 2. 爬取详情页

```bash
cd scripts
python tripadvisor_scraper_v2.py <restaurant_id>
```

或使用 crawl4ai:
```bash
uv pip install crawl4ai
python scripts/crawl_ta_single.py
```

## 📋 待办事项

- [ ] 详情页地址 + 排名字段补充 (高优先级)
- [ ] 详情页子评分补充
- [ ] 评论区数据提取管道
- [ ] 多语言支持 (英文名/英文地址)
- [ ] 数据清洗与标准化输出

## 📄 许可

数据仅供研究学习使用，请遵守 TripAdvisor 服务条款。

## 🔗 相关链接

- TripAdvisor 香港餐厅: https://www.tripadvisor.cn/Restaurants-g294217-Hong_Kong.html
- XOOTOUR Spec V1: https://cuplore.com/view.php?file=XOO/XOOTOUR-RESTAURANT-SPEC-V1
