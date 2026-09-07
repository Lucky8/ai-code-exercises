# ScrapeMaster FAQ

ScrapeMaster is a flexible Python web scraping framework for defining, scheduling, processing, and exporting scraping jobs. This FAQ is written for beginner and intermediate developers.

> **Responsible use:** Only scrape sites and data that you are authorized to access. Follow applicable laws, terms of service, privacy requirements, rate limits, and `robots.txt` directives.

## Getting Started

### What is ScrapeMaster?

ScrapeMaster provides a configuration-driven way to crawl web pages, extract structured data, process the results, and export them to files or databases. It combines Scrapy, BeautifulSoup, SQLAlchemy, Celery, and Redis for crawling, parsing, persistence, and scheduling.

### What do I need before installing ScrapeMaster?

You need Python 3.7 or later, `pip`, Redis, and network access to the sites you are authorized to scrape. A virtual environment is recommended so that ScrapeMaster dependencies do not conflict with other Python projects.

### How do I install the dependencies?

From the project directory, create and activate a virtual environment, then install the dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows PowerShell, activate the environment with:

```powershell
.venv\Scripts\Activate.ps1
```

If the project does not include a requirements file, install the core packages directly:

```bash
pip install scrapy beautifulsoup4 sqlalchemy celery redis pyyaml requests
```

### Why does ScrapeMaster require Redis?

Redis is used by Celery as a message broker and, depending on the deployment configuration, as a result backend. It allows scheduled jobs and worker processes to communicate without running in the same process.

Start Redis locally with:

```bash
redis-server
```

Or run it with Docker:

```bash
docker run --name scrapemaster-redis -p 6379:6379 -d redis:7
```

### How do I run my first scraper?

Create a YAML configuration with a name, starting URL, extraction rules, and export destination. Then run it with the project command:

```bash
python -m scrapemaster run --config config/products.yml
```

The exact command may vary if the application exposes a different entry point.

### Where should configuration files go?

Keep shared configuration in `config/` and example jobs in `examples/`. Store secrets in environment variables or a secret manager instead of committing them to YAML or JSON files.

### Is there a Python API as well as configuration files?

Yes. A scraper can be defined in Python when configuration files are not expressive enough for custom logic:

```python
from scrapemaster import ScrapeMaster

scraper = ScrapeMaster(
    name="products",
    start_urls=["https://example.com/products"],
    extraction={"name": {"css": ".product-name::text"}},
    export={"format": "json", "destination": "output/products.json"},
)

scraper.run()
```

## Features and Functionality

### Which extraction methods are supported?

ScrapeMaster supports CSS selectors and XPath expressions. Use CSS for readable selectors and XPath when you need more precise relationships or attribute matching.

```yaml
extract:
  title:
    css: "h1.product-title::text"
  canonical_url:
    xpath: "//link[@rel='canonical']/@href"
```

### How do I extract a list of records?

Select a parent element and define fields relative to each item:

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

### Can ScrapeMaster process extracted data before exporting it?

Yes. Processors can validate, clean, normalize, deduplicate, or enrich items before an exporter writes them. Use the `scrapemaster/processors` package for reusable pipelines and keep site-specific transformations close to the relevant scraper definition.

### Which export formats are available?

The documented exporters support CSV, JSON, and databases through SQLAlchemy:

```yaml
export:
  format: json
  destination: output/items.json
```

For a database export:

```yaml
export:
  format: database
  table: scraped_items
  database_url: ${DATABASE_URL}
```

### Can I export to SQLite?

Yes, if the SQLAlchemy database exporter supports the configured URL. A typical SQLite URL is:

```text
sqlite:///output/scrapemaster.db
```

Make sure the output directory exists and that the application process has write permission.

### How do I schedule a scraper?

Add a cron expression and timezone to the job configuration:

```yaml
schedule:
  cron: "0 */6 * * *"
  timezone: "UTC"
```

Run the scheduler and a Celery worker in the deployment environment:

```bash
python -m scrapemaster scheduler start
celery -A scrapemaster.scheduler worker --loglevel=info
```

### What does the cron expression mean?

The expression `0 */6 * * *` runs at minute zero every six hours. Always check the configured timezone, especially when a job must run at a business-specific local time.

### How do retries and request delays work?

`retries` controls how many times a failed request is retried. `timeout` limits how long a request may wait, and `download_delay` spaces requests apart. For example:

```yaml
requests:
  timeout: 30
  retries: 3
download_delay: 1.0
```

Use a reasonable delay and concurrency value to avoid overloading a target site.

### Can I rotate proxies and user agents?

Yes. Configure approved proxies and user agents, then enable rotation:

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
```

Rotation does not grant permission to bypass authentication, access controls, rate limits, or anti-bot protections. Keep credentials out of configuration files.

### How is CAPTCHA handling configured?

CAPTCHA handling is disabled by default. When it is permitted and required, configure an approved provider or a manual review flow:

```yaml
captcha:
  enabled: true
  provider: manual
  max_attempts: 2
  timeout: 120
```

Do not use CAPTCHA handling to evade protections on sites you are not authorized to access.

### How do I receive job notifications?

Configure a webhook URL and select the events that should trigger notifications:

```yaml
notifications:
  enabled: true
  webhook_url: ${SCRAPEMASTER_WEBHOOK_URL}
  events:
    - job_started
    - job_completed
    - job_failed
```

Store the webhook URL in an environment variable and verify that the receiving service accepts the payload format used by the application.

### Does ScrapeMaster execute JavaScript?

Scrapy and BeautifulSoup do not execute browser JavaScript by themselves. If the required content is absent from the server response, inspect the site's supported API or use an authorized browser-rendering integration that matches the project architecture.

### What is the recommended project structure?

The main directories are:

- `scrapemaster/scrapers`: scraper definitions and crawl rules.
- `scrapemaster/extractors`: CSS and XPath extraction tools.
- `scrapemaster/processors`: validation and transformation pipelines.
- `scrapemaster/exporters`: CSV, JSON, and database exporters.
- `scrapemaster/scheduler`: Celery tasks and recurring jobs.
- `scrapemaster/utils`: shared configuration, logging, and request helpers.
- `config`: YAML or JSON job configuration.
- `examples`: example scraper definitions.

## Troubleshooting

### Redis connection errors

Check that Redis is running and reachable:

```bash
redis-cli ping
```

A working local Redis instance returns `PONG`. Also check the configured Redis host, port, password, and `REDIS_URL` environment variable.

### The scraper runs but extracts no data

Verify the selector against the HTML response received by the scraper, not only the browser's rendered DOM. Check for redirects, challenge pages, changed markup, incorrect nesting, and JavaScript-loaded content.

### The scraper gets a `403` or `429` response

Reduce concurrency, increase the download delay, respect the site's rate limits, and verify that the scraper is authorized. Check whether the request headers, proxy configuration, or user agent are invalid. Do not attempt to circumvent access restrictions.

### The output file is empty or missing

Confirm that extraction produced items, the export format is spelled correctly, and the destination directory exists. Check that the process has permission to write to the destination and inspect the job log for exporter errors.

### Database export fails

Check that the SQLAlchemy URL is valid, the required database driver is installed, the database is reachable, and the configured user can create or write to the target table. For SQLite, verify the parent directory and file permissions.

### Scheduled jobs do not run

Confirm that Redis, the scheduler, and at least one Celery worker are running. Check the worker logs for import or serialization errors, verify the cron expression, and make sure the scheduler loaded the intended configuration file.

### Webhook notifications fail

Validate the webhook URL and inspect its HTTP response status. Confirm that outbound network access is available and that the receiving service accepts the payload. Keep webhook secrets out of logs and source control.

### Requests time out

Increase the timeout only when the target is known to respond slowly. First check DNS, network connectivity, proxy health, server availability, and whether the URL redirects to an inaccessible location. Keep retries bounded so one job cannot run indefinitely.

### A configuration file is rejected

Check YAML indentation, quoting, key names, and environment variable syntax. Compare the file with a known working example and validate that required values such as `name`, `start_urls`, and export settings are present.

### The worker cannot import `scrapemaster`

Activate the intended virtual environment, install the project and its dependencies in that environment, and run the command from the project root. Check that the Celery `-A` value points to the actual application module.

### A job produces duplicate records

Review pagination and retry behavior, then add a stable item identifier and a deduplication processor or database uniqueness constraint. A retry should not create a second record for the same source item.

### A token, password, or webhook secret was committed

Revoke or rotate the exposed secret immediately, remove it from the active configuration, and inspect repository history according to your organization's incident-response process. Adding the file to `.gitignore` does not remove a secret already committed.

## Best Practices

- Begin with a small, read-only scraper and a limited URL set.
- Use configuration files for simple jobs and Python APIs for custom logic.
- Set explicit timeouts, bounded retries, delays, and concurrency limits.
- Log job status and item counts without logging credentials or private payloads.
- Test selectors against representative HTML and update them when site markup changes.
- Store secrets in environment variables or a dedicated secret manager.
- Validate and normalize data before exporting it.
- Make scheduled jobs and exporters idempotent where possible.
- Monitor failed jobs, rate limits, webhook deliveries, and token expiration.
- Follow the target site's terms, `robots.txt`, and applicable privacy and data-protection requirements.

## Still Need Help?

When reporting a problem, include the ScrapeMaster version, Python version, operating system, configuration keys involved, a redacted error message, and the smallest reproducible example. Do not include tokens, passwords, proxy credentials, webhook secrets, or private scraped data.
