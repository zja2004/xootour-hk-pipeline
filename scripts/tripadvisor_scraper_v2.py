#!/usr/bin/env python3
"""
TripAdvisor V2 Spec Scraper for XOOTOUR Hong Kong restaurants.
Extracts all L1-L5 fields per V2 spec, with token usage tracking.

Usage:
    python tripadvisor_scraper_v2.py --test          # Test 1 restaurant (AOAO)
    python tripadvisor_scraper_v2.py --all           # All 30 with TA URLs
    python tripadvisor_scraper_v2.py --url <url>     # Single custom URL
"""

import asyncio
import json
import re
import sys
import time
import random
import hashlib
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional

import httpx
from bs4 import BeautifulSoup

# --- Token tracking ---
@dataclass
class TokenStats:
    url: str = ""
    input_chars: int = 0
    output_chars: int = 0
    http_requests: int = 0
    elapsed_seconds: float = 0.0
    # Estimated tokens (rough: 1 token ≈ 4 chars English, 2 chars Chinese)
    @property
    def estimated_input_tokens(self) -> int:
        return self.input_chars // 4
    
    @property
    def estimated_output_tokens(self) -> int:
        return self.output_chars // 4
    
    @property
    def estimated_total_tokens(self) -> int:
        return self.estimated_input_tokens + self.estimated_output_tokens

# --- V2 Spec Data Model ---
@dataclass
class RestaurantV2:
    # L1 基础信息
    restaurant_id: str = ""
    name_zh: str = ""
    name_en: str = ""
    name_original: str = ""
    cuisines: list = field(default_factory=list)
    price_level: str = ""  # ¥ ~ ¥¥¥¥
    price_range_hkd: str = ""
    phone: str = ""
    website: str = ""
    description: str = ""
    
    # L2 位置信息
    address_zh: str = ""
    address_en: str = ""
    district: str = ""
    latitude: float = 0.0
    longitude: float = 0.0
    landmark_proximity: list = field(default_factory=list)
    
    # L3 评分与评论
    rating: float = 0.0
    review_count: int = 0
    rank: str = ""  # e.g. "第 15 名，共 15,000 家"
    sub_ratings: dict = field(default_factory=dict)  # {食物: 4.5, 服务: 4.2, ...}
    
    # L4 服务信息
    opening_hours: dict = field(default_factory=dict)
    payment_methods: list = field(default_factory=list)
    language_support: list = field(default_factory=list)
    special_diets: list = field(default_factory=list)  # vegetarian, gluten-free, etc.
    certifications: list = field(default_factory=list)  # Michelin, etc.
    
    # L5 质量与血源
    source_url: str = ""
    source_platform: str = "tripadvisor.cn"
    crawled_at: str = ""
    data_quality_score: float = 0.0  # 0-100
    photos_count: int = 0
    photos_urls: list = field(default_factory=list)


class TripAdvisorScraperV2:
    """Scrapes TripAdvisor restaurant detail pages to V2 spec."""
    
    TA_RESTAURANT_PATTERN = re.compile(r'tripadvisor\.cn/Restaurant_Review-')
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    ]
    
    def __init__(self, output_dir: str = "/root/.hermes/dogfood-output/xooer"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.token_log: list[TokenStats] = []
        
    def _random_delay(self, min_s=1.0, max_s=3.0):
        time.sleep(random.uniform(min_s, max_s))
    
    def _get_client(self) -> httpx.Client:
        return httpx.Client(
            headers={
                "User-Agent": random.choice(self.USER_AGENTS),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
                "Cache-Control": "max-age=0",
            },
            follow_redirects=True,
            timeout=30.0,
        )
    
    def _extract_restaurant_id(self, url: str) -> str:
        """Extract TA restaurant ID from URL."""
        m = re.search(r'd(\d+)', url)
        return m.group(1) if m else hashlib.md5(url.encode()).hexdigest()[:8]
    
    def scrape_single(self, url: str) -> tuple[Optional[RestaurantV2], TokenStats]:
        """Scrape a single restaurant detail page."""
        stats = TokenStats(url=url)
        t_start = time.time()
        
        # Validate URL
        if not self.TA_RESTAURANT_PATTERN.search(url):
            print(f"  SKIP: Not a TA restaurant URL: {url}")
            return None, stats
        
        rest = RestaurantV2()
        rest.source_url = url
        rest.crawled_at = datetime.now().isoformat()
        rest.restaurant_id = self._extract_restaurant_id(url)
        
        try:
            with self._get_client() as client:
                # Step 1: Fetch main page
                t0 = time.time()
                resp = client.get(url)
                stats.http_requests += 1
                
                if resp.status_code != 200:
                    print(f"  HTTP {resp.status_code} for {url}")
                    return None, stats
                
                html = resp.text
                stats.input_chars += len(html)
                soup = BeautifulSoup(html, 'lxml')
                self._random_delay(0.3, 0.8)
                
                # Step 2: Extract basic info
                self._extract_basic_info(soup, rest, html)
                self._extract_location(soup, rest, html)
                self._extract_ratings(soup, rest, html)
                self._extract_services(soup, rest, html)
                self._extract_photos(soup, rest, html)
                
                # Step 3: Quality score
                self._compute_quality_score(rest)
                
                stats.output_chars += len(json.dumps(asdict(rest), ensure_ascii=False))
                stats.elapsed_seconds = time.time() - t_start
                self.token_log.append(stats)
                
                return rest, stats
                
        except Exception as e:
            print(f"  ERROR scraping {url}: {e}")
            stats.elapsed_seconds = time.time() - t_start
            return None, stats
    
    def _extract_basic_info(self, soup: BeautifulSoup, rest: RestaurantV2, html: str):
        """Extract L1 basic info: name, cuisine, price, phone, website, description."""
        # Name - try multiple selectors
        name_selectors = [
            '[data-test-target="top-info-header"]',
            'h1',
            '[class*="HjBfq"]',
            '[class*="restaurantName"]',
        ]
        for sel in name_selectors:
            el = soup.select_one(sel)
            if el and len(el.get_text(strip=True)) > 1:
                rest.name_zh = el.get_text(strip=True)
                rest.name_en = rest.name_zh  # TA.cn often shows both
                break
        
        # Also regex from body text for Chinese name format
        body = soup.get_text()
        # Try pattern: "XXX(香港)" or detect lang mix
        name_matches = re.findall(r'(.{2,40})\s*(?:\(香港\))?', body[:500])
        
        # Cuisine tags
        cuisine_links = soup.select('a[href*="/Restaurants-"]')
        seen_cuisines = set()
        for a in cuisine_links:
            txt = a.get_text(strip=True)
            if txt and len(txt) < 30 and not any(kw in txt.lower() for kw in ['香港', 'hong kong', '中菜', '所有']):
                seen_cuisines.add(txt)
        rest.cuisines = list(seen_cuisines)[:10]
        
        # Price level
        price_match = re.search(r'[¥￥]{1,4}', body[:3000])
        if price_match:
            rest.price_level = price_match.group(0)
        
        # Price range (e.g., "HK$200-400")
        price_range_match = re.search(r'(?:HK\$|HKD|港幣)\s*[\d,]+[-–~]\s*[\d,]+', body[:3000])
        if price_range_match:
            rest.price_range_hkd = price_range_match.group(0)
        
        # Phone
        phone_match = re.search(r'(\+852[\s-]?\d{4}[\s-]?\d{4}|\d{4}[\s-]?\d{4})', body[:5000])
        if phone_match:
            rest.phone = phone_match.group(0)
        
        # Website
        website_links = soup.select('a[href*="://"]')
        for a in website_links:
            href = a.get('href', '')
            if any(kw in href for kw in ['.com', '.hk', '.net']) and not any(skip in href for skip in ['tripadvisor', 'google', 'facebook']):
                rest.website = href
                break
        
        # Description (first long text paragraph)
        paras = soup.select('p, div[class*="description"], div[class*="overview"]')
        for p in paras:
            txt = p.get_text(strip=True)
            if len(txt) > 80 and len(txt) < 2000:
                rest.description = txt
                break
    
    def _extract_location(self, soup: BeautifulSoup, rest: RestaurantV2, html: str):
        """Extract L2 location: address, district, coordinates."""
        body = soup.get_text()
        
        # Address - pattern "地址：xxx" or in JSON-LD
        addr_match = re.search(r'地址[：:]\s*(.+?)(?:\n|。|，|$)', body[:5000])
        if not addr_match:
            addr_match = re.search(r'(香港[\u4e00-\u9fff\w\s,，、]+?(?:道|街|路|坊|廣場|中心|大廈|商場)[\u4e00-\u9fff\w\s,]*)', body[:5000])
        if addr_match:
            rest.address_zh = addr_match.group(1).strip()
        
        # District
        districts = ['中環', '尖沙咀', '銅鑼灣', '旺角', '灣仔', '上環', '金鐘', 
                     '九龍城', '觀塘', '荃灣', '元朗', '沙田', '大埔', '屯門',
                     '香港仔', '赤柱', '淺水灣', '西貢', '大嶼山', '天后', '炮台山']
        for d in districts:
            if d in (rest.address_zh + body[:2000]):
                rest.district = d
                break
        
        # Coordinates from meta/script tags
        coord_patterns = [
            r'"latitude":\s*"?([\d.]+)"?',
            r'"lat":\s*"?([\d.]+)"?',
            r'center:\s*\{\s*lat:\s*([\d.]+)',
            r'data-lat="([\d.]+)"',
        ]
        for pat in coord_patterns:
            m = re.search(pat, html)
            if m:
                rest.latitude = float(m.group(1))
                break
        
        coord_lng_patterns = [
            r'"longitude":\s*"?([\d.]+)"?',
            r'"lng":\s*"?([\d.]+)"?',
            r'center:\s*\{\s*lat:\s*[\d.]+,\s*lng:\s*([\d.]+)',
            r'data-lng="([\d.]+)"',
        ]
        for pat in coord_lng_patterns:
            m = re.search(pat, html)
            if m:
                rest.longitude = float(m.group(1))
                break
        
        # Landmark proximity
        landmarks = ['維港', '天星碼頭', '山頂', '迪士尼', '海洋公園', '蘭桂坊', 
                     '廟街', '女人街', '黃大仙', '星光大道', 'M+', '故宮']
        for lm in landmarks:
            if lm in body[:10000]:
                rest.landmark_proximity.append(lm)
    
    def _extract_ratings(self, soup: BeautifulSoup, rest: RestaurantV2, html: str):
        """Extract L3 ratings, reviews, rank, sub-ratings."""
        body = soup.get_text()
        
        # Rating - look for number patterns near "评分" or "bubble"
        # TA.cn format: "4.5 1,384条点评"
        rating_match = re.search(r'(\d+\.\d+)\s*(?:分)?[\s\u00a0]*(?:共)?[\s\u00a0]*([\d,]+)\s*条点评', body[:5000])
        if rating_match:
            rest.rating = float(rating_match.group(1))
            rest.review_count = int(rating_match.group(2).replace(',', ''))
        else:
            # Try generic number search
            rating_match = re.search(r'(\d\.\d)[\s\u00a0]*([\d,]+)\s*条', body[:5000])
            if rating_match:
                rest.rating = float(rating_match.group(1))
                rest.review_count = int(rating_match.group(2).replace(',', ''))
        
        # Try rate attributes (TA's star rating system)
        rate_match = re.search(r'rate["\']?\s*:\s*["\']?(\d+)', html)
        if rate_match and rest.rating == 0:
            rest.rating = float(rate_match.group(1)) / 10.0
        
        # Rank
        rank_match = re.search(r'第\s*(\d+)\s*名.*?共\s*([\d,]+)', body[:5000])
        if rank_match:
            rest.rank = f"第 {rank_match.group(1)} 名，共 {rank_match.group(2)} 家"
        
        # Sub-ratings (food, service, atmosphere, value)
        sub_rating_labels = {
            '食物': 'food', '美食': 'food', '菜式': 'food', '料理': 'food',
            '服務': 'service', '服务': 'service',
            '氛圍': 'atmosphere', '氛围': 'atmosphere', '環境': 'atmosphere', '环境': 'atmosphere',
            '價值': 'value', '价值': 'value', '性價比': 'value', '性价比': 'value',
        }
        # Find sub-rating bubbles via aria-label
        aria_ratings = re.findall(r'aria-label=["\']([^"\']*(?:食物|服務|氛圍|價值|美食|服务|氛围|环境|价值|性价比).*?(\d+\.?\d*)[^"\']*)["\']', html)
        for aria_text, score in aria_ratings:
            for zh, en in sub_rating_labels.items():
                if zh in aria_text:
                    rest.sub_ratings[en] = float(score)
                    break
        
        # Also sub-rating rate attributes
        sub_rate_matches = re.findall(r'(?:subRating|sub_rating).*?rate["\']?\s*:\s*["\']?(\d+)', html)
        # These are often in fixed order: food, service, atmosphere, value
        keys = ['food', 'service', 'atmosphere', 'value']
        for i, rate_val in enumerate(sub_rate_matches[:4]):
            if keys[i] not in rest.sub_ratings:
                rest.sub_ratings[keys[i]] = float(rate_val) / 10.0
    
    def _extract_services(self, soup: BeautifulSoup, rest: RestaurantV2, html: str):
        """Extract L4 services: hours, payments, languages, diets, certifications."""
        body = soup.get_text()
        
        # Opening hours
        hour_patterns = [
            r'(?:營業時間|开放时间|時間)[：:]*\s*(.+?)(?:\n\n|\n[A-Z])',
            r'(?:週一|周一|星期一).*?(\d{1,2}:\d{2})\s*[-–]\s*(\d{1,2}:\d{2})',
        ]
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        zh_days = ['週一', '周一', '週二', '周二', '週三', '周三', '週四', '周四', 
                   '週五', '周五', '週六', '周六', '週日', '周日', '星期日']
        
        for zh_day, en_day in zip(zh_days[::2] + zh_days[1::2] + ['星期日'], days + days + ['sunday']):
            pattern = f'{zh_day}[\\s:：]*([\\d:]+)\\s*[-–~]\\s*([\\d:]+)'
            m = re.search(pattern, body[:8000])
            if m:
                rest.opening_hours[en_day] = f"{m.group(1)}-{m.group(2)}"
        
        # Payment methods
        payment_kw = {
            'visa': ['visa', 'Visa', 'VISA'],
            'mastercard': ['mastercard', 'MasterCard', 'master', 'Master'],
            'amex': ['amex', 'American Express', 'AE', '運通'],
            'alipay': ['alipay', 'Alipay', '支付寶', '支付宝'],
            'wechat_pay': ['wechat', 'WeChat', '微信支付'],
            'unionpay': ['unionpay', 'UnionPay', '銀聯', '银联'],
            'cash': ['cash', '現金', '现金'],
            'apple_pay': ['apple pay', 'Apple Pay'],
            'octopus': ['八達通', '八达通', 'Octopus'],
        }
        found_payments = set()
        for method, keywords in payment_kw.items():
            for kw in keywords:
                if kw.lower() in body.lower()[:8000] or kw in html[:10000]:
                    found_payments.add(method)
                    break
        rest.payment_methods = sorted(found_payments)
        
        # Language support
        lang_kw = {
            'zh': ['中文', '普通話', '廣東話', '粵語', '國語'],
            'en': ['英文', 'English', '英語'],
            'ja': ['日文', '日本語', 'Japanese'],
            'ko': ['韓文', '한국어', 'Korean'],
        }
        found_langs = set()
        for lang, keywords in lang_kw.items():
            for kw in keywords:
                if kw in body[:8000] or kw in html[:10000]:
                    found_langs.add(lang)
                    break
        rest.language_support = sorted(found_langs) if found_langs else ['zh', 'en']
        
        # Special diets
        diet_kw = ['素食', 'vegetarian', 'vegan', 'gluten-free', '無麩質', '清真', 'halal',
                   '猶太', 'kosher', '有機', 'organic']
        for kw in diet_kw:
            if kw.lower() in body.lower()[:8000]:
                rest.special_diets.append(kw)
        
        # Certifications (Michelin, Black Pearl, etc.)
        cert_kw = {
            'michelin_1_star': ['米其林一星', 'Michelin one star', '1 star michelin'],
            'michelin_2_star': ['米其林二星', '二星', '2 star'],
            'michelin_3_star': ['米其林三星', '三星', '3 star'],
            'michelin_bib': ['必比登', 'Bib Gourmand'],
            'black_pearl': ['黑珍珠', 'Black Pearl'],
            'asia_50_best': ['Asia\'s 50 Best', '亞洲50最佳'],
            'world_50_best': ['World\'s 50 Best'],
        }
        for cert, keywords in cert_kw.items():
            for kw in keywords:
                if kw.lower() in body.lower()[:8000]:
                    rest.certifications.append(cert)
                    break
    
    def _extract_photos(self, soup: BeautifulSoup, rest: RestaurantV2, html: str):
        """Extract photo count and URLs."""
        # Photo count
        photo_match = re.search(r'(\d+)\s*(?:張照片|张照片|照片|photos|Photos)', soup.get_text()[:5000])
        if photo_match:
            rest.photos_count = int(photo_match.group(1))
        
        # Photo URLs (large format)
        photo_urls = set()
        for img in soup.select('img[src]'):
            src = img.get('src', '')
            if 'media-cdn.tripadvisor.com' in src or 'static.tacdn.com' in src:
                # Convert to large format
                large_url = re.sub(r'photo-[wol]', 'photo-l', src)
                photo_urls.add(large_url)
        rest.photos_urls = sorted(photo_urls)[:20]
        
        # Count from URL patterns too
        if rest.photos_count == 0 and photo_urls:
            rest.photos_count = len(photo_urls)
    
    def _compute_quality_score(self, rest: RestaurantV2):
        """Compute L5 data quality score (0-100)."""
        score = 0
        
        # Completeness (max 50)
        if rest.name_zh: score += 10
        if rest.address_zh: score += 10
        if rest.rating > 0: score += 10
        if rest.review_count > 0: score += 5
        if rest.cuisines: score += 5
        if rest.price_level: score += 5
        if rest.sub_ratings: score += 5
        
        # Richness (max 30)
        if rest.latitude and rest.longitude: score += 10
        if rest.description: score += 10
        if rest.photos_count > 0: score += 5
        if rest.opening_hours: score += 5
        
        # Authenticity (max 20)
        if rest.certifications: score += 10
        if rest.payment_methods: score += 5
        if rest.language_support: score += 5
        
        rest.data_quality_score = min(score, 100)
    
    def scrape_all(self, urls: list[str]) -> dict:
        """Scrape all restaurants and return results with token stats."""
        results = []
        all_stats = []
        
        print(f"\n{'='*60}")
        print(f"Starting bulk scrape of {len(urls)} restaurants")
        print(f"{'='*60}\n")
        
        for i, url in enumerate(urls):
            print(f"[{i+1}/{len(urls)}] {url.split('/')[-1][:60]}...")
            
            restaurant, stats = self.scrape_single(url)
            
            if restaurant:
                results.append(asdict(restaurant))
                all_stats.append(stats)
                print(f"  ✓ {restaurant.name_zh[:40]} | ★{restaurant.rating} | {restaurant.review_count} reviews | Q={restaurant.data_quality_score}")
                print(f"  📊 Tokens: ~{stats.estimated_total_tokens} (in={stats.estimated_input_tokens}, out={stats.estimated_output_tokens})")
            else:
                print(f"  ✗ FAILED")
            
            # Save incrementally
            if results:
                with open(self.output_dir / "hk_restaurants_v2.json", 'w') as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
                with open(self.output_dir / "token_stats.json", 'w') as f:
                    json.dump([asdict(s) for s in all_stats], f, ensure_ascii=False, indent=2)
            
            # Random delay between requests
            if i < len(urls) - 1:
                delay = random.uniform(2, 6)
                print(f"  ⏳ Waiting {delay:.1f}s...")
                time.sleep(delay)
        
        # Summary
        total_input_tokens = sum(s.estimated_input_tokens for s in all_stats)
        total_output_tokens = sum(s.estimated_output_tokens for s in all_stats)
        total_tokens = total_input_tokens + total_output_tokens
        avg_tokens = total_tokens / len(all_stats) if all_stats else 0
        
        summary = {
            "total_restaurants": len(urls),
            "successful": len(results),
            "failed": len(urls) - len(results),
            "total_estimated_tokens": total_tokens,
            "avg_tokens_per_restaurant": round(avg_tokens, 1),
            "input_tokens": total_input_tokens,
            "output_tokens": total_output_tokens,
            "avg_quality_score": round(sum(r.get('data_quality_score', 0) for r in results) / len(results), 1) if results else 0,
        }
        
        print(f"\n{'='*60}")
        print(f"SMMARY")
        print(f"{'='*60}")
        for k, v in summary.items():
            print(f"  {k}: {v}")
        
        with open(self.output_dir / "scrape_summary.json", 'w') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        return summary


def load_urls(data_file: str) -> list[str]:
    """Load TripAdvisor URLs from merged dataset."""
    with open(data_file) as f:
        data = json.load(f)
    
    urls = []
    for r in data:
        url = r.get('tripadvisor_url')
        if url and 'tripadvisor.cn/Restaurant_Review' in url:
            urls.append(url)
    return urls


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--test', action='store_true', help='Test with AOAO')
    parser.add_argument('--all', action='store_true', help='Scrape all TA URLs')
    parser.add_argument('--url', type=str, help='Single custom URL')
    parser.add_argument('--data', type=str, 
                        default='/root/.hermes/dogfood-output/xooer/hk_restaurants_merged.json',
                        help='Path to merged data')
    args = parser.parse_args()
    
    scraper = TripAdvisorScraperV2()
    
    if args.url:
        urls = [args.url]
    elif args.test:
        # Find AOAO's URL
        with open(args.data) as f:
            data = json.load(f)
        aoa = next((r for r in data if 'AOAO' in (r.get('name_en') or '')), None)
        if not aoa:
            aoa = next((r for r in data if r.get('tripadvisor_url')), None)
        urls = [aoa['tripadvisor_url']] if aoa else []
        print(f"Test target: {aoa.get('name_zh', 'Unknown')} → {urls[0]}")
    elif args.all:
        urls = load_urls(args.data)
    else:
        parser.print_help()
        sys.exit(0)
    
    if not urls:
        print("No URLs to scrape!")
        sys.exit(1)
    
    scraper.scrape_all(urls)
