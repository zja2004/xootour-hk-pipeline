# XOOTOUR Hong Kong Data Pipeline

香港餐厅+景点数据采集、评分、推荐管线，按 [XOOTOUR-RESTAURANT-SPEC-V2](https://cuplore.com/view.php?file=XOO/XOOTOUR-RESTAURANT-SPEC-V2) 标准。

## 数据概况

| 类别 | 数量 | 来源 |
|------|------|------|
| 餐厅 (V2 Spec) | 30 | TripAdvisor.cn 实时爬取 |
| 餐厅 (合并) | 95 | TA + AI 生成融合 |
| 景点 | 20 | 手工采集 |

## 爬取结果 (最新)

```
成功率: 100% (30/30)
总Token: 713,135
均店Token: 23,771
平均质量分: 63.7/100
```

## 技术栈

见 [TECHSTACK.md](TECHSTACK.md)

## 数据源可行性

见 [FEASIBILITY_REPORT.md](FEASIBILITY_REPORT.md)

## 目录结构

```
repo/
├── data/
│   ├── raw/           # 原始数据 (merged, restaurants, attractions)
│   └── processed/     # 处理后数据 (V2 spec, token stats, summary)
├── scripts/           # 爬虫脚本
│   └── tripadvisor_scraper_v2.py
├── TECHSTACK.md       # 技术栈总结
├── FEASIBILITY_REPORT.md  # 可行性评估
└── README.md
```

## 快速开始

```bash
# 环境
/root/.hermes/hermes-agent/venv/bin/python3
uv pip install beautifulsoup4 lxml httpx

# 测试单店
cd scripts && python tripadvisor_scraper_v2.py --test

# 全量爬取
python tripadvisor_scraper_v2.py --all
```
