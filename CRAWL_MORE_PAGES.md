# How to Crawl Multiple Pages

The crawler is working correctly, but it's set to MINIMAL mode which only crawls very few pages to prevent system overload.

## Why Only 1 Page Was Crawled

When you see "1 pages crawled", it's because:

1. **Minimal mode active** - `CRAWLER_CONCURRENT_REQUESTS=1` means only 1 page at a time
2. **High delay** - `CRAWLER_DOWNLOAD_DELAY=2` means 2 seconds between each page
3. **Possibly low depth** - If depth was set to 1, it won't follow links

## Solution: Use Balanced Mode

### Stop Current Server
```bash
# Press Ctrl+C in the terminal where server is running
# Or run:
./emergency_stop.sh
```

### Start with Balanced Crawling
```bash
chmod +x start_balanced.sh
./start_balanced.sh
```

This enables:
- **4 concurrent requests** (crawl 4 pages simultaneously)
- **5 levels deep** (follows links up to 5 levels)
- **1 second delay** (faster than 2 seconds)
- Still resource-controlled (won't crash system)

### Trigger a New Crawl

```bash
# Crawl a specific domain with better settings
curl -X POST http://localhost:8000/api/v1/crawl \
  -H "Content-Type: application/json" \
  -d '{
    "domains": ["bakkah.net"]
  }'
```

### Monitor Progress

**Terminal 1** - Watch resources:
```bash
htop
# Or: watch -n 2 'ps aux | grep python | head -3'
```

**Terminal 2** - Watch logs:
```bash
tail -f data/logs/crawler.log
```

You should now see:
```
Starting crawl for domain: bakkah.net
Found 0 URLs in sitemap for bakkah.net
Crawling page: https://bakkah.net/
Found 15 links on page...
Crawling page: https://bakkah.net/about
Crawling page: https://bakkah.net/courses
...
Completed crawl for bakkah.net: 42 pages crawled, 2 failed
```

## Configuration Levels

### 1. Minimal (Current - 1-2 pages)
```bash
./start_minimal.sh
# CRAWLER_CONCURRENT_REQUESTS=1
# CRAWLER_DOWNLOAD_DELAY=2
# MAX_CRAWL_DEPTH=3
```

### 2. Balanced (Recommended - 20-50 pages)
```bash
./start_balanced.sh
# CRAWLER_CONCURRENT_REQUESTS=4
# CRAWLER_DOWNLOAD_DELAY=1
# MAX_CRAWL_DEPTH=5
```

### 3. Aggressive (100+ pages, higher risk)
```bash
# Set environment variables:
export CRAWLER_CONCURRENT_REQUESTS=8
export CRAWLER_DOWNLOAD_DELAY=0.5
export MAX_CRAWL_DEPTH=7
export MAX_EMBEDDING_BATCH_SIZE=64

./start_safe.sh
```

## Understand Crawl Depth

**Depth 1**: Only home page
**Depth 2**: Home page + pages linked from home
**Depth 3**: Above + pages linked from those pages
**Depth 5**: Can reach ~50-100 pages on typical sites

Example with bakkah.net:
- Depth 1: `bakkah.net/` (1 page)
- Depth 2: `bakkah.net/`, `/about`, `/courses`, `/contact` (4 pages)
- Depth 3: Above + `/courses/python`, `/courses/data-science`, etc. (20 pages)
- Depth 5: Full site navigation (50-200 pages)

## Check What Settings Are Active

```bash
curl http://localhost:8000/api/v1/status | python -m json.tool
```

Look for:
```json
{
  "settings": {
    "max_crawl_depth": 5,
    "crawler_concurrent_requests": 4,
    "crawler_download_delay": 1
  }
}
```

## Why Crawl Might Stop Early

1. **Robots.txt blocking** - Site says "don't crawl"
   - Check: `curl https://bakkah.net/robots.txt`
   - Disable: Set `RESPECT_ROBOTS_TXT=False` (not recommended)

2. **No internal links** - Site uses JavaScript navigation
   - Check logs for "Found X links"
   - Solution: Limited - crawler can't execute JavaScript

3. **All links external** - Site links to other domains
   - Crawler only follows same-domain links
   - This is correct behavior

4. **Hit depth limit**
   - Increase `MAX_CRAWL_DEPTH` to 7 or 10

## Recommended Workflow

1. **Start balanced**: `./start_balanced.sh`
2. **Test crawl**: Crawl 1 domain
3. **Monitor**: Watch memory/CPU for 5 minutes
4. **If stable**: Continue with more domains
5. **If unstable**: Go back to minimal mode

## Quick Compare

| Mode | Pages/Domain | Time/Domain | Memory | Risk |
|------|--------------|-------------|--------|------|
| Minimal | 1-5 | 30 sec | Low | None |
| Balanced | 20-50 | 2-5 min | Medium | Low |
| Aggressive | 100+ | 10-20 min | High | Medium |

---

**Current Status**: You're in MINIMAL mode
**Recommendation**: Switch to BALANCED mode with `./start_balanced.sh`
**Expected Result**: 20-50 pages per domain instead of just 1
