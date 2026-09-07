# ScrapeMaster

ScrapeMaster is a flexible Python web scraping framework for defining, scheduling, processing, and exporting scraping jobs. It supports configuration-driven scrapers, resilient request handling, structured data extraction, and notifications when jobs complete or fail.

## Features

- Define scrapers with a simple YAML or JSON configuration format.
- Schedule recurring scraping jobs.
- Rotate proxies and switch user agents to distribute requests.
- Integrate CAPTCHA handling into scraping workflows.
- Extract data with CSS selectors or XPath expressions.
- Process and transform scraped items through pipelines.
- Export results to CSV, JSON, or a database through SQLAlchemy.
- Send webhook notifications for job status, errors, and completion.
- Use Scrapy for crawling and BeautifulSoup for HTML parsing when needed.
- Run scheduled work through Celery with Redis as the broker and result backend.

## Requirements

- Python 3.7 or later
- `pip`
- Redis
- Network access to the sites being scraped
- Permission to scrape the target sites and comply with their terms of service and `robots.txt`

## Installation

### 1. Clone the project

```bash
git clone https://github.com/your-org/scrapemaster.git
cd scrapemaster
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on macOS or Linux:

```bash
source .venv/bin/activate
```

Activate it on Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

If a requirements file is not yet included, install the core dependencies directly:

```bash
pip install scrapy beautifulsoup4 sqlalchemy celery redis pyyaml requests
```

### 4. Start Redis

With a local Redis installation:

```bash
redis-server
```

Or with Docker:

```bash
docker run --name scrapemaster-redis -p 6379:6379 -d redis:7
```

### 5. Configure the environment

Copy the example configuration and update its values:

```bash
cp config/config.example.yml config/config.yml
```

On Windows PowerShell:

```powershell
Copy-Item config\config.example.yml config\config.yml
```

Do not commit credentials, proxy passwords, or webhook secrets to source control.

## Quick Start

### Configuration-driven scraper

Create `config/products.yml`:

```yaml
name: products
start_urls:
  - https://example.com/products

requests:
  user_agents:
    - "Mozilla/5.0 (compatible; ScrapeMaster/1.0)"
  timeout: 30
  retries: 3

extract:
  products:
    selector: ".product"
    fields:
      name:
        css: ".product-name::text"
      price:
        css: ".price::text"
      url:
        css: "a::attr(href)"

export:
  format: json
  destination: output/products.json

notifications:
  webhook_url: ${SCRAPEMASTER_WEBHOOK_URL}
```

Run the scraper with the command-line entry point:

```bash
python -m scrapemaster run --config config/products.yml
```

The exact command may vary depending on how the application entry point is packaged.

### Python API

A scraper can also be defined in Python:

```python
from scrapemaster import ScrapeMaster

scraper = ScrapeMaster(
    name="products",
    start_urls=["https://example.com/products"],
    extraction={
        "name": {"css": ".product-name::text"},
        "price": {"css": ".price::text"},
        "url": {"css": "a::attr(href)"},
    },
    export={
        "format": "json",
        "destination": "output/products.json",
    },
)

scraper.run()
```

### XPath extraction

CSS selectors and XPath can be used together:

```yaml
extract:
  title:
    xpath: "//h1[@class='product-title']/text()"
  description:
    css: ".description::text"
```

### Scheduling a job

Add a schedule to a scraper configuration:

```yaml
schedule:
  cron: "0 */6 * * *"
  timezone: "UTC"
```

Start the scheduler and Celery worker according to the deployment environment:

```bash
python -m scrapemaster scheduler start
celery -A scrapemaster.scheduler worker --loglevel=info
```

## Configuration

Configuration can be supplied as YAML or JSON. Values can be overridden with environment variables where supported.

### General options

| Option | Description | Example |
| --- | --- | --- |
| `name` | Unique scraper or job name. | `products` |
| `start_urls` | URLs from which crawling begins. | `["https://example.com"]` |
| `allowed_domains` | Domains the crawler may visit. | `["example.com"]` |
| `concurrency` | Maximum simultaneous requests. | `4` |
| `download_delay` | Delay between requests in seconds. | `1.0` |
| `timeout` | Request timeout in seconds. | `30` |
| `retries` | Number of failed request retries. | `3` |

### Request and access options

```yaml
requests:
  proxies:
    - http://proxy-one.example:8080
    - http://proxy-two.example:8080
  rotate_proxies: true
  user_agents:
    - "Mozilla/5.0 ..."
    - "ScrapeMasterBot/1.0"
  rotate_user_agents: true
  headers:
    Accept-Language: en-US
```

Proxy and user-agent rotation should be used responsibly. Do not use them to bypass access controls or site restrictions.

### CAPTCHA handling

CAPTCHA handling is disabled by default. When enabled, configure an approved provider or a manual review workflow:

```yaml
captcha:
  enabled: true
  provider: manual
  max_attempts: 2
  timeout: 120
```

Only use CAPTCHA services and automated access methods that comply with the target site's policies and applicable laws.

### Extraction options

Each field can use `css` or `xpath`. A collection can be selected with a parent selector and then mapped into fields:

```yaml
extract:
  articles:
    xpath: "//article"
    fields:
      headline:
        css: "h2::text"
      link:
        xpath: ".//a/@href"
```

### Export options

```yaml
export:
  format: csv                 # csv, json, or database
  destination: output/items.csv
  encoding: utf-8
```

For database exports, configure SQLAlchemy using an environment variable:

```yaml
export:
  format: database
  table: scraped_items
  database_url: ${DATABASE_URL}
```

Example database URL:

```text
sqlite:///output/scrapemaster.db
```

For production databases, use the connection URL appropriate for the installed SQLAlchemy driver.

### Webhook notifications

```yaml
notifications:
  enabled: true
  webhook_url: ${SCRAPEMASTER_WEBHOOK_URL}
  events:
    - job_started
    - job_completed
    - job_failed
```

Webhook payloads should include the job name, status, item count, duration, and error details when applicable.

## Project Structure

```text
scrapemaster/
├── __init__.py
├── scrapers/       # Scraper definitions and crawl rules
├── extractors/     # CSS and XPath data extraction tools
├── processors/     # Data cleaning and processing pipelines
├── exporters/      # CSV, JSON, and SQLAlchemy export modules
├── scheduler/      # Celery tasks and recurring job scheduling
└── utils/          # Shared configuration, logging, and request utilities
config/             # YAML or JSON configuration files
examples/           # Example scraper definitions and usage
```

A typical job flows through the framework as follows:

1. The scheduler starts a configured job.
2. The scraper requests pages while applying retries, delays, proxy rotation, and user-agent selection.
3. Extractors select fields with CSS selectors or XPath.
4. Processors validate and normalize the extracted items.
5. Exporters write the results to CSV, JSON, or a database.
6. The notification service sends the job result to the configured webhook.

## Troubleshooting

### Redis connection errors

Confirm that Redis is running and that the configured host and port are reachable:

```bash
redis-cli ping
```

A healthy local installation returns `PONG`. Check `REDIS_URL` if the application uses an environment-based connection string.

### No items are extracted

- Verify that the selector matches the HTML returned by the server.
- Inspect the page source rather than only the browser's rendered DOM.
- Check whether the content is loaded by JavaScript; Scrapy and BeautifulSoup do not execute JavaScript by themselves.
- Confirm that the response status is successful and that the request is not being redirected to a challenge page.

### Requests are blocked or rate-limited

Reduce concurrency, increase `download_delay`, enable retries, and use an approved proxy configuration. Always respect the target site's terms, rate limits, and `robots.txt`.

### Database export fails

Check that the SQLAlchemy connection URL is valid, the required database driver is installed, and the target user has permission to create or write to the configured table.

### Scheduled jobs do not run

- Confirm that both Redis and the Celery worker are running.
- Check the worker log for import or serialization errors.
- Verify the cron expression and timezone.
- Make sure the scheduler is loading the intended configuration file.

### Webhook notifications fail

Validate the webhook URL, inspect the HTTP response status, and confirm that outbound network access is allowed. Keep webhook secrets in environment variables rather than configuration files committed to Git.

## Contributing

Contributions are welcome.

1. Fork the repository and create a focused feature branch.
2. Install development dependencies and run the existing test suite.
3. Add or update tests for behavior you change.
4. Keep public APIs and configuration changes documented.
5. Run formatting, linting, and tests before opening a pull request.
6. Describe the problem, the implementation, and any configuration changes in the pull request.

Please do not include real credentials, private data, or unauthorized target-site content in issues, examples, or tests.

## License

ScrapeMaster is intended to be distributed under the MIT License. Add the repository's `LICENSE` file with the complete license text before publishing a release. See the license file in the repository for the authoritative terms.

## Responsible Use

Use ScrapeMaster only on sites and data that you are authorized to access. Follow applicable laws, terms of service, privacy requirements, rate limits, and `robots.txt` directives. ScrapeMaster does not grant permission to bypass authentication, access controls, or anti-bot protections.
