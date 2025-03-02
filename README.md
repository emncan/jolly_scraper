# Scrapy + Selenium Tourism Scraper

This repository contains a Scrapy project that uses Selenium to scrape tourism data from a JS-heavy website (specifically [jollytur.com](https://www.jollytur.com/)). Because the site’s content is dynamically loaded (JavaScript-driven), we integrate Selenium for full rendering, allowing Scrapy to extract the necessary information. The project also demonstrates various Scrapy middlewares and a custom scoring pipeline.

## Features

1. **Combining Scrapy and Selenium**  
   - We utilize Selenium to handle dynamically loaded content.  
   - Scrapy orchestrates the overall crawling, including scheduling requests and parsing items.

2. **Middleware Usage**  
   - **RandomUserAgentMiddleware**: Assigns a random User-Agent to each request to emulate different browsers and possibly bypass basic anti-scraping measures.  
   - **ProxyMiddleware**: Example middleware for routing requests through different proxies. *(Currently disabled in `settings.py` due to non-working proxy IPs; shown only as a reference.)*

3. **ScorePipeline**  
   - Collects all scraped items, calculates a custom “final_score” for each (based on price, features, etc.), then saves only the top 10 results to a JSON file.

## Project Structure
```bash
JOLLY_SCRAPER
├── scraper
│   ├── output
│   └── scraper
│       ├── spiders
│       │   ├── __init__.py
│       │   └── jolly_spider.py
│       ├── __init__.py
│       ├── items.py
│       ├── middlewares.py
│       ├── pipelines.py
│       ├── settings.py
│       ├── jolly_selenium.py
│       └── scoring.py
├── .gitignore
├── scrapy.cfg
├── README.md
└── requirements.txt
```
## Installation

1. **Clone this repository** (or download the project files).
2. **Install Python dependencies:** 
    ```bash
    pip install -r requirements.txt
    ```
3. **(Optional) Adjust Settings**
    - In ```settings.py```, you can enable/disable custom middlewares or configure the proxy list as needed.
    - By default, ```ProxyMiddleware``` is commented out. This is because the example proxies in the code may not work reliably. You can uncomment the line in ```DOWNLOADER_MIDDLEWARES``` if you have valid proxies.

## Usage
From the project’s root directory, you can run the spider using:

```bash
    scrapy crawl jolly -a destination=Ölüdeniz -a target_month=Haziran -a target_year=2025 -a checkin_day=10 -a checkout_day=14 -a adult_count=3 -o output/Ölüdeniz.json
```

## Explanation of Arguments
- **destination**: Desired travel location (in Turkish, e.g., "Kuşadası").
- **target_month**: Month name (Turkish) for check-in (e.g., "Haziran").
- **target_year**: Year for check-in (e.g., "2025").
- **checkin_day**: Day of check-in (e.g., "10").
- **checkout_day**: Day of check-out (e.g., "14").
- **adult_count**: Number of adults (e.g., "3").

Scrapy will parse these parameters, pass them to the Selenium driver to perform the search, and then scrape the results.

**Note: The script is designed to be flexible. You can modify these parameters as needed to scrape different destinations and time ranges.**

## Proxy & User-Agent Middlewares

- **RandomUserAgentMiddleware**
    - In middlewares.py, this class picks a random User-Agent from a predefined list (```USER_AGENT_LIST``` in ```settings.py```).
    - Activated in ```settings.py``` with:
        ```bash
            DOWNLOADER_MIDDLEWARES = {
            # "scraper.middlewares.ProxyMiddleware": 400,
            "scraper.middlewares.RandomUserAgentMiddleware": 410,
            }
        ```

- **ProxyMiddleware**
    - Example code for rotating proxies.
    - Currently commented out in ```settings.py``` since the sample proxies are not guaranteed to work.
    - If you have valid proxies, you can uncomment the middleware entry and update the ```PROXY_LIST``` setting.


## Custom Scoring
For demonstration, each hotel’s ```final_score``` is computed by:

1. **parse_price**  
   - Converts price strings in Turkish format (e.g. `"43.990,00 TL"`) into float values (e.g. `43990.00`).  
   - Removes the `" TL"` suffix, replaces commas with dots for decimals, and strips out thousands separators.

2. **compute_base_score**  
   - Looks at several factors to build a base score:
     1. If the `cancel_policy` contains `"Risksiz rezervasyon"`, add **+1**.  
     2. If `recomended_hotel` is **not** null, add **+1**.  
     3. Count the number of features in `hotel_features` and add **0.05** for each one.  
     4. Depending on `accommodation_types`, add:  
        - **+2.0** for `"Ultra Her Şey Dahil"`  
        - **+1.5** for `"Her Şey Dahil"`  
        - **+1.0** for `"Yarım Pansiyon"`  
        - **+0.5** for `"Oda Kahvaltı"`  
        - **+0.3** for `"Sadece Oda"`

3. **Final Score**  
   - After computing the `base_score`, the final score is derived by dividing `base_score` by the parsed price (to reflect overall value).

4. **Results**  
   - All results are saved to the `output` folder. The raw results are written to a file named `<destination>.json`, and the top 10 scored results are in `<destination>_scored.json`.