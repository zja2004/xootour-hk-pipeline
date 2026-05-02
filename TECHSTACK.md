# XOOTOUR HK Data Pipeline — 技术栈总结

## 项目概述
为 XOOTOUR 构建香港餐厅+景点数据采集管线，按 XOOTOUR-RESTAURANT-SPEC-V2 标准采集、清洗、评分。

## 技术栈

### 核心工具
| 组件 | 技术 | 用途 |
|------|------|------|
| 爬虫框架 | Python 3.11 + BeautifulSoup4 + httpx | TripAdvisor HTML 解析和数据提取 |
| 无头浏览器 | Playwright (Chromium) | 小红书等JS渲染页面的备用方案 |
| AI爬虫 | crawl4ai | 备选的LLM辅助结构化提取 |
| 数据处理 | Python stdlib (json, re, hashlib, dataclasses) | 数据标准化、质量评分 |
| 包管理 | uv (pip-compatible) | Python 依赖管理，venv隔离 |
| 版本控制 | Git + GitHub SSH | 代码、数据、文档的持久化存储 |

### 数据源评估结果
| 平台 | 状态 | Token/页 | 说明 |
|------|------|----------|------|
| **TripAdvisor.cn** | ✅ 主力 | ~24k | 30家真实URL，纯HTML直接解析，无验证墙 |
| **小红书** | ⚠️ 备用 | TBD | SSR页面472KB，需Playwright渲染；API端点404 |
| **大众点评** | ❌ 不可用 | N/A | 美团验证码墙 (verify.meituan.com/spiderindefence) |
| **美团** | ❌ 不可用 | N/A | HK站为企业官网；移动端API需登录+签名 |
| **OpenRice** | ❌ 不可用 | N/A | Cloudflare防护 |

### V2 Spec 数据模型 (5层)
- **L1 基础信息**: 名称(中/英), 菜系, 价格, 电话, 网站, 描述
- **L2 位置信息**: 地址(中/英), 区域, 经纬度, 地标
- **L3 评分评论**: 综合评分, 点评数, 排名, 子评分(食物/服务/氛围/性价比)
- **L4 服务信息**: 营业时间, 支付方式, 语言支持, 特殊饮食, 认证(米其林/黑珍珠)
- **L5 质量血缘**: 数据源URL, 来源平台, 采集时间, 数据质量分(0-100)

### 数据质量评分体系
- 完整性 (50分): name, address, rating, reviews, cuisines, price, sub_ratings
- 丰富度 (30分): coordinates, description, photos, hours
- 真实性 (20分): certifications, payments, languages

### Token 消耗估算
- 单店: ~23,782 tokens (输入 23,532 + 输出 250)
- 30家全量: ~713,460 tokens
- 100家估算: ~2.38M tokens

### 输出文件
```
data/
├── hk_restaurants_v2.json    # V2规格结构化数据
├── token_stats.json          # Token消耗统计
├── scrape_summary.json       # 爬取汇总
└── feasibility_report.json   # 数据源可行性评估
```

### 环境配置
```bash
# Python venv
/root/.hermes/hermes-agent/venv/bin/python3
# 包安装 (uv)
uv pip install <pkg> --python /root/.hermes/hermes-agent/venv/bin/python3
# 浏览器
playwright install chromium
```
