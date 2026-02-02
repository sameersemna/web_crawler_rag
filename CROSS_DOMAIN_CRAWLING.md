# Cross-Domain Crawling Feature

## Overview

The crawler now intelligently follows links to **other approved domains** listed in `domains.csv`. This enables natural discovery of related content across your approved knowledge base without requiring separate crawl jobs.

## How It Works

### Before (Single-Domain Only)
When crawling `domain-a.com`:
- ✅ Links to `domain-a.com/page1` → **Crawled**
- ✅ Links to `subdomain.domain-a.com` → **Crawled**
- ❌ Links to `domain-b.com` → **Skipped** (even if in domains.csv)

### After (Cross-Domain for Approved Domains)
When crawling `domain-a.com`:
- ✅ Links to `domain-a.com/page1` → **Crawled**
- ✅ Links to `subdomain.domain-a.com` → **Crawled**
- ✅ Links to `domain-b.com` → **Crawled** (if `domain-b.com` is in domains.csv)
- ❌ Links to `random-site.com` → **Skipped** (not in domains.csv)

## Benefits

### 1. **Natural Content Discovery**
Related websites often link to each other. If you're crawling Islamic knowledge sites, one site might reference another's fatwa or article. The crawler now follows these connections automatically.

### 2. **Better Coverage**
You don't need to manually find every page on every domain. The crawler discovers content through the natural link structure.

### 3. **Unified Knowledge Base**
Content from multiple related domains is seamlessly integrated into a single, interconnected knowledge base.

### 4. **Efficient Crawling**
No need for separate crawl jobs per domain. Start crawling one domain, and it naturally discovers content from related approved domains.

## Example Scenario

**domains.csv:**
```csv
domain
islamqa.info
islamweb.net
islamhouse.com
```

**Crawl Process:**

1. Start crawling `islamqa.info`
2. On `islamqa.info/fatwa/12345`, find link to `islamweb.net/article/456`
3. Crawler recognizes `islamweb.net` is in domains.csv ✓
4. Crawler follows link and saves `islamweb.net/article/456`
5. On `islamweb.net/article/456`, find link to `islamhouse.com/book/789`
6. Crawler recognizes `islamhouse.com` is in domains.csv ✓
7. Crawler follows link and saves `islamhouse.com/book/789`

**Result:** All three sites' content is crawled and linked together, even though you only started with one domain.

## Technical Implementation

### 1. **Approved Domain Cache**
On startup, the crawler loads all domains from the database into memory:
```python
await self._load_approved_domains()
# Result: {'islamqa.info', 'islamweb.net', 'islamhouse.com', ...}
```

### 2. **Link Extraction Logic**
When extracting links from a page:
```python
# Check if link is from same domain (as before)
if self._is_same_domain(url, base_url):
    links.add(url)
    
# NEW: Also check if link is from another approved domain
elif self._is_approved_domain(url):
    links.add(url)
    log("Including cross-domain link from approved domain")
```

### 3. **Domain Assignment**
Pages are saved with their actual domain (extracted from URL):
```python
actual_domain = self._get_domain_from_url(url)  # e.g., "islamweb.net"
await self._save_page(domain=actual_domain, url=url, ...)
```

This ensures:
- Pages are attributed to the correct domain in the database
- Filtering by domain works correctly in queries
- Statistics are accurate per domain

## Logging

The crawler logs cross-domain discoveries:

```
[INFO] Including cross-domain link from approved domain: https://islamweb.net/article/456
[INFO] Including cross-domain link from approved domain: https://islamhouse.com/book/789
[INFO] Link extraction from https://islamqa.info/fatwa/12345: 50 anchors found, 5 cross-domain approved links, 12 different domain, 43 total links
```

## Configuration

No configuration needed! The feature works automatically:

1. **Add domains to domains.csv**
   ```csv
   domain
   site-a.com
   site-b.com
   site-c.com
   ```

2. **Start crawling any domain**
   ```bash
   # Crawl site-a, it will automatically follow links to site-b and site-c
   python main_crawl.py config_islam.yaml
   ```

3. **Monitor logs** to see cross-domain links being discovered

## Database Schema

Pages are stored with correct domain attribution:

| domain | url | title | content |
|--------|-----|-------|---------|
| islamqa.info | https://islamqa.info/fatwa/12345 | Ruling on... | ... |
| islamweb.net | https://islamweb.net/article/456 | Article about... | ... |
| islamhouse.com | https://islamhouse.com/book/789 | Book on... | ... |

## Query Filtering

Domain filtering still works correctly:

```python
# Query only islamqa.info content
POST /api/v1/query-filtered
{
    "query": "What is the ruling on...",
    "domains": ["islamqa.info"]
}

# Query multiple domains
POST /api/v1/query-filtered
{
    "query": "What is the ruling on...",
    "domains": ["islamqa.info", "islamweb.net"]
}
```

## Safety Features

### 1. **Whitelist Only**
Only domains explicitly listed in `domains.csv` are crawled. Random external links are still ignored.

### 2. **No Infinite Loops**
The existing visited URL tracking prevents re-crawling:
```python
if url in self.visited_urls:
    continue  # Already crawled
```

### 3. **Depth Limits**
The `max_crawl_depth` setting still applies, preventing endless crawling.

### 4. **Robots.txt Compliance**
Cross-domain links still respect robots.txt of the target domain.

## Performance Impact

### Minimal Overhead
- Domain list loaded once at startup (cached in memory)
- Domain check is O(n) where n = number of approved domains (typically < 100)
- No additional database queries per link

### Increased Crawl Coverage
- May crawl more pages (discovering cross-domain content)
- May take longer to complete initial crawl
- Results in more comprehensive knowledge base

## Use Cases

### 1. **Related Websites Network**
Crawl a network of related Islamic knowledge sites that reference each other.

### 2. **Official Subdomains**
A site might have separate subdomains for different topics:
- `main.example.com`
- `articles.example.com`
- `books.example.com`

### 3. **Citation Networks**
Legal or academic sites that cite each other's documents.

### 4. **Multi-Language Content**
Sites that link to translations on separate domains:
- `english.site.com` → links to → `arabic.site.com`

## Monitoring

Check crawl statistics to see cross-domain discoveries:

```bash
# View domains in database
sqlite3 data/law/crawler_rag.db "SELECT domain, COUNT(*) as pages FROM crawled_pages GROUP BY domain;"

# Output:
# islamqa.info|1250
# islamweb.net|430
# islamhouse.com|890
```

## Limitations

1. **Same Instance Only**: Cross-domain crawling only works within the same instance (e.g., all domains in `data/islam/domains.csv` can link together, but not to domains in `data/law/domains.csv`)

2. **One-Way Links**: If `domain-a.com` has no links to `domain-b.com`, content from `domain-b.com` won't be discovered unless you explicitly crawl it or another domain links to it

3. **Depth Limit**: Very distant cross-domain links (beyond max_crawl_depth hops) won't be reached

## Best Practices

1. **Start with Hub Sites**: Begin crawling from sites that link to many other approved domains (hub sites)

2. **Verify Domains**: Ensure all domains in domains.csv are actually related and should share a knowledge base

3. **Monitor First Crawl**: Watch the logs during the first crawl to see which cross-domain links are discovered

4. **Adjust Depth**: Increase `max_crawl_depth` if you're not reaching all desired cross-domain content

## Troubleshooting

### Cross-domain links not being followed?

**Check logs for:**
```
[DEBUG] Skipping different domain: https://example.com
```

**Solutions:**
1. Verify domain is in `domains.csv`
2. Check domain name matches (with/without `www.`)
3. Ensure crawler has loaded approved domains (check startup logs)

### Too many pages being crawled?

**If crawler is discovering too much cross-domain content:**
1. Reduce `max_crawl_depth` in config
2. Remove unwanted domains from `domains.csv`
3. Use domain-specific crawl jobs instead

### Performance issues?

**If crawling is slower than expected:**
1. The increased coverage is intentional - you're getting more content
2. Increase `crawler_concurrent_requests` for faster crawling
3. Consider separate instances for unrelated domain groups

## Future Enhancements

Potential improvements:
- [ ] Cross-instance domain linking
- [ ] Domain relationship strength scoring
- [ ] Configurable cross-domain depth limits
- [ ] Cross-domain link analytics/visualization

---

**Summary**: The crawler now intelligently discovers and crawls content across all your approved domains, creating a more comprehensive and interconnected knowledge base automatically. Simply add domains to domains.csv, and the crawler handles the rest! 🚀
