# XOOTOUR HK — 数据源可行性评估报告

**生成时间**: 2026-05-03  
**上下文**: XOOTOUR HK 餐厅数据收集项目  

## 终极结论
**唯一可靠的主力数据源：TripAdvisor 中文站 (tripadvisor.cn)**

---

## 各平台评估详情

### 1. TripAdvisor 中文站 (tripadvisor.cn) ✅ **主力源**
- **爬取方式**: 纯 HTTP GET + BeautifulSoup HTML 解析
- **无需**: 浏览器渲染、Cookie 维持、登录
- **数据量**: 已确认30家真实URL（可扩展到更多）
- **单店Token**: ~23,782 tokens (输入 ~23.5k, 输出 ~250)
- **提取质量**: 可提取V2 Spec全部L1-L5层
- **风险**: 偶发CAPTCHA（未遇到）；反爬策略温和
- **推荐**: **立即规模化为100+家**

### 2. 小红书 (xiaohongshu.com) ⚠️ **备用源**
- **爬取方式**: 需要 Playwright 无头浏览器
- **页面**: 搜索页返回 472KB SSR HTML，数据在 JS 渲染后
- **API**: edith.xiaohongshu.com API 返回 404（路径已废弃或需签名）
- **可行性**: 技术可行但工程量大，数据结构非标准化
- **推荐**: 可在TripAdvisor稳定后探索，用于补充用户UGC评价

### 3. 大众点评 (dianping.com) ❌ **不可用**
- **HTTP状态**: 200 但重定向到 verify.meituan.com
- **防御**: 美团团 spiderindefence 验证码墙
- **结论**: 无法绕过，放弃

### 4. 美团 (meituan.com) ❌ **不可用**
- **hk.meituan.com**: 企业官网（首页、社会责任、投资者关系），无餐厅数据
- **移动端API**: apimobile.meituan.com 返回 404
- **i.meituan.com**: 返回蜘蛛防御页
- **结论**: HK站无数据，放弃

### 5. OpenRice (openrice.com) ❌ **不可用**
- **防御**: Cloudflare 5秒盾 + 浏览器检查
- **结论**: 工程成本高，ROI低，放弃

---

## 执行路线图

### Phase 1: TripAdvisor 规模化 (当前) ✅
- [x] 单店测试 (AOAO, 24k tokens)
- [ ] 30家全量爬取 (运行中)
- [ ] 扩展到100家搜索

### Phase 2: 小红书探索 (待定)
- [ ] Playwright 渲染可行性验证
- [ ] 结构化提取 PoC

### Phase 3: 数据融合
- [ ] 多源交叉验证
- [ ] 质量评分矩阵
