#!/usr/bin/env python3
"""Batch crawl TripAdvisor detail pages via __NEXT_DATA__ (SSR, no JS needed)"""
import json, urllib.request, re, time, os, sys
from concurrent.futures import ThreadPoolExecutor, as_completed

def slugify(name):
    slug = re.sub(r'[^a-zA-Z0-9\s]', '', name)
    slug = re.sub(r'\s+', '_', slug.strip())
    return slug or 'restaurant'

def fetch_detail_page(restaurant, idx=0):
    rid = restaurant['restaurantId']
    name = restaurant.get('name', f'restaurant-{rid}')
    slug = slugify(name)
    url = f"https://www.tripadvisor.cn/Restaurant_Review-g294217-d{rid}-Reviews-{slug}-Hong_Kong.html"
    
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0', 'Accept-Language': 'zh-CN,zh;q=0.9'
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode('utf-8', errors='replace')
        
        match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html)
        if not match:
            return {'restaurantId': rid, 'error': 'no __NEXT_DATA__'}
        
        nd = json.loads(match.group(1))
        hm = nd['props']['pageProps']['initialState']['staticData']['headerModels']
        sd = nd['props']['pageProps']['initialState']['staticData']
        
        return {
            'restaurantId': rid,
            'name': hm.get('name'),
            'address': hm.get('address'),
            'latitude': hm.get('latitude'),
            'longitude': hm.get('longitude'),
            'rating': hm.get('rating'),
            'reviewCount': hm.get('numReviews'),
            'price': (hm.get('priceLevel') or {}).get('priceLevel'),
            'ranking': hm.get('ranking'),
            'rankingString': hm.get('rankingString'),
            'rankingOutOf': hm.get('rankingOutOf'),
            'status': (hm.get('restaurantHours') or {}).get('businessStatus'),
            'hours': (hm.get('restaurantHours') or {}).get('taFormatTimes'),
            'phone': hm.get('phone'),
            'website': hm.get('website'),
            'email': hm.get('email'),
            'meals': (sd.get('details') or {}).get('meals'),
            'features': (sd.get('details') or {}).get('features'),
            'cuisines': [c.get('name') for c in (sd.get('headerCuisine') or [])],
            'subratings': [
                {'name': s.get('ratingName'), 'value': s.get('ratingValue')}
                for s in (sd.get('subratings') or [])
            ],
            'photoCount': (sd.get('photos') or {}).get('totalPhotoCount'),
            'awards': [a.get('displayName') for a in (sd.get('awards') or [])]
        }
    except Exception as e:
        return {'restaurantId': rid, 'error': str(e)[:200]}

def main():
    # Load restaurant list
    with open('hk_restaurants_api_list.json', 'r') as f:
        data = json.load(f)
    restaurants = data['restaurants']
    total = len(restaurants)
    print(f"Loaded {total} restaurants")

    # Resume from checkpoint if exists
    checkpoint_file = 'batch_checkpoint.json'
    results = []
    processed_ids = set()
    if os.path.exists(checkpoint_file):
        with open(checkpoint_file) as f:
            results = json.load(f)
        processed_ids = {r['restaurantId'] for r in results}
        print(f"Resumed from checkpoint: {len(results)} already processed")

    remaining = [r for r in restaurants if r['restaurantId'] not in processed_ids]
    print(f"Remaining: {len(remaining)}")

    start = time.time()
    errors = 0
    batch_size = 500
    completed = len(results)

    with ThreadPoolExecutor(max_workers=20) as executor:
        for batch_start in range(0, len(remaining), batch_size):
            batch = remaining[batch_start:batch_start + batch_size]
            futures = {executor.submit(fetch_detail_page, r): r for r in batch}
            
            for future in as_completed(futures):
                result = future.result()
                if 'error' in result:
                    errors += 1
                results.append(result)
                completed += 1
            
            # Save checkpoint every batch
            with open(checkpoint_file, 'w') as f:
                json.dump(results, f, ensure_ascii=False)
            
            elapsed = time.time() - start
            rate = completed / elapsed if elapsed > 0 else 0
            remaining_count = total - completed
            eta = remaining_count / rate if rate > 0 else 0
            
            print(f"Progress: {completed}/{total} ({100*completed/total:.1f}%), "
                  f"Rate: {rate:.1f} req/s, Errors: {errors}, ETA: {eta:.0f}s")

    # Final save
    output_file = 'hk_restaurants_detail.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, ensure_ascii=False)
    
    # Stats
    success = [r for r in results if 'error' not in r]
    failed = [r for r in results if 'error' in r]
    
    print(f"\n=== Final Results ===")
    print(f"Total: {len(results)}, Success: {len(success)}, Failed: {len(failed)}")
    print(f"Time: {time.time()-start:.1f}s")
    print(f"Output: {output_file} ({os.path.getsize(output_file)/1024:.0f} KB)")

if __name__ == '__main__':
    main()
