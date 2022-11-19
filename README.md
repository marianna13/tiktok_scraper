# TikTok Scraper
Python TikTok video URLs scraper

Scrapes TikTok usernames, video descriptions and URLs. Works by discovering new tags from TikTok "For You" page or from "seed_tags" tag pages. It's possible to specify the number of pages per tag or depth (with num_pages_per_url parameter).

Example:
`@adidas,pov: football thirst trap #football #soccer #worldcup #adidas,https://www.tiktok.com/@adidas/video/7080945096862043397`

# Requirements
```
numpy
pandas
requests
beautifulsoup4
tqdm
```

# Usage
```python
from tiktok_scraper import TikTokScraper

scraper = TikTokScraper(num_process=3)
scraper(
    num_pages_per_url=2,
    data_path='META.csv'
)
```

With seed tags:
```python
scraper(
    seed_tags=['worldcup', 'newyork'],
    num_pages_per_url=2,
    data_path='META.csv'
)
```
