# GitHub Integration Guide

This guide explains how to connect the application to GitHub for repository access and GitHub-based workflows. It is written for **beginner users** and assumes that the application provides a GitHub integration configuration screen or equivalent environment variables.

> **Security reminder:** Never share a personal access token in chat, source code, screenshots, issue comments, or committed configuration files.

## Prerequisites

Before you begin, confirm that you have:

- An active GitHub account.
- Permission to access the GitHub organization or repository that the application will use.
- Repository administrator or organization administrator access if you need to configure webhooks or an OAuth app.
- Access to the application's administrator settings or deployment environment.
- The repository owner and name, for example `acme/scrapemaster`.
- A secure place to store secrets, such as environment variables or a secrets manager.
- Network access from the application to `api.github.com` and the relevant GitHub endpoints.

[Placeholder: Screenshot of the required GitHub account, repository, and application administrator access]

## Integration Overview

The integration normally uses one of these authentication methods:

- **Fine-grained personal access token:** Suitable for a single user or controlled internal setup. Grant access only to the required repositories and permissions.
- **GitHub App:** Recommended for production or organization-wide integrations. It provides repository-scoped permissions and installation-based access.
- **OAuth app:** Useful when multiple users authorize the application with their own GitHub accounts.

Use the authentication method required by your application's integration settings. The steps below use a fine-grained personal access token because it is the simplest option for a first setup.

## Step-by-Step Setup

### 1. Identify the target repository

1. Open the repository in GitHub.
2. Copy the repository owner and name from the URL.
3. Record the default branch, such as `main` or `master`.
4. Decide which operations the application needs:
   - Read repository files or metadata.
   - Create or update issues.
   - Read or write pull requests.
   - Receive webhook events.
   - Push commits or create branches.

Start with read-only access. Add write permissions only when the application requires them.

[Placeholder: Screenshot showing the GitHub repository URL, owner, name, and default branch]

### 2. Create a fine-grained personal access token

1. In GitHub, open **Settings**.
2. Select **Developer settings**.
3. Select **Personal access tokens** and then **Fine-grained tokens**.
4. Select **Generate new token**.
5. Enter a descriptive name, such as `ScrapeMaster integration`.
6. Set an expiration date. Short-lived tokens are safer and should be renewed before they expire.
7. Under **Resource owner**, select the correct account or organization.
8. Under **Repository access**, choose **Only select repositories** and select the target repository.
9. Grant only the permissions required by the application. Typical read-only permissions include:
   - **Metadata:** Read-only.
   - **Contents:** Read-only if the application reads files.
   - **Issues:** Read and write only if the application manages issues.
   - **Pull requests:** Read and write only if the application manages pull requests.
10. Select **Generate token**.
11. Copy the token immediately and store it in your secret manager. GitHub will not display the full token again.

[Placeholder: Screenshot of the fine-grained token repository access and permissions page]

### 3. Configure the application secret

Set the token in the environment where the application runs. Do not paste it directly into Python files, YAML committed to Git, or a public CI configuration.

Example `.env` values:

```dotenv
GITHUB_TOKEN=github_pat_your_token_here
GITHUB_REPOSITORY_OWNER=acme
GITHUB_REPOSITORY_NAME=scrapemaster
GITHUB_DEFAULT_BRANCH=main
```

Example YAML configuration:

```yaml
github:
  enabled: true
  repository: acme/scrapemaster
  default_branch: main
  token_env: GITHUB_TOKEN
```

The `token_env` setting tells the application to read the secret from the `GITHUB_TOKEN` environment variable rather than storing the token in the configuration file.

If the application uses a web interface:

1. Open the administrator settings.
2. Select **Integrations** or **GitHub**.
3. Enter the repository owner and name.
4. Select the authentication method.
5. Enter the token into the password or secret field.
6. Save the configuration.

[Placeholder: Screenshot of the application's GitHub integration settings]

### 4. Restart or reload the application

Many applications read environment variables only during startup. Restart the application or reload its configuration after adding the GitHub settings.

For a local Python process, restart the process after setting the variables:

```bash
python -m scrapemaster
```

For a service managed by Docker Compose:

```bash
docker compose up -d --force-recreate
```

For a process manager or hosted deployment, use the platform's normal restart or redeploy action.

### 5. Test the connection

Use the application's **Test connection** action if one is available. A successful test should confirm the authenticated account and target repository without exposing the token.

A generic API test with `curl` looks like this:

```bash
curl --fail-with-body \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer ${GITHUB_TOKEN}" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  "https://api.github.com/repos/${GITHUB_REPOSITORY_OWNER}/${GITHUB_REPOSITORY_NAME}"
```

On Windows PowerShell:

```powershell
$headers = @{
  Accept = "application/vnd.github+json"
  Authorization = "Bearer $env:GITHUB_TOKEN"
  "X-GitHub-Api-Version" = "2022-11-28"
}

Invoke-RestMethod `
  -Headers $headers `
  -Uri "https://api.github.com/repos/$env:GITHUB_REPOSITORY_OWNER/$env:GITHUB_REPOSITORY_NAME"
```

The response should include repository metadata such as `full_name` and `default_branch`. Do not paste the complete response into a public issue if it contains private repository information.

[Placeholder: Screenshot of a successful connection test with the token redacted]

### 6. Run a small application workflow

Start with a read-only operation, such as listing repository metadata or reading a known documentation file. Example Python code using the GitHub REST API:

```python
import os

import requests

repository = "acme/scrapemaster"
url = f"https://api.github.com/repos/{repository}"
headers = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}",
    "X-GitHub-Api-Version": "2022-11-28",
}

response = requests.get(url, headers=headers, timeout=30)
response.raise_for_status()

repository_data = response.json()
print(repository_data["full_name"])
print(repository_data["default_branch"])
```

Replace this example with the application's built-in GitHub action or service call when one exists. Avoid testing write operations until the read-only connection works.

### 7. Configure webhooks, if required

Webhooks allow GitHub to notify the application when events occur, such as a push, issue update, or pull request change.

1. Make sure the application has a public HTTPS endpoint for GitHub to reach.
2. Open the repository in GitHub and select **Settings**.
3. Select **Webhooks** and then **Add webhook**.
4. Enter the application's webhook URL.
5. Choose `application/json` as the content type.
6. Create a strong webhook secret and configure the same secret in the application.
7. Select only the events the application needs, such as **Pushes** or **Pull requests**.
8. Save the webhook.
9. Use **Recent deliveries** to send a test delivery and inspect the response.

Example webhook settings:

```dotenv
GITHUB_WEBHOOK_SECRET=store_this_in_a_secret_manager
GITHUB_WEBHOOK_URL=https://app.example.com/webhooks/github
```

The application must verify the `X-Hub-Signature-256` header before processing a webhook payload. Never trust an incoming webhook solely because it came from an accessible URL.

[Placeholder: Screenshot of the GitHub webhook configuration page with the secret hidden]

### 8. Verify the complete workflow

Perform one normal workflow from start to finish:

1. Make a harmless change in the test repository, such as updating a documentation line.
2. Push the change or trigger the configured GitHub event.
3. Confirm that GitHub records a successful webhook delivery, if webhooks are enabled.
4. Confirm that the application receives and processes the event.
5. Check the application log for the repository name, event type, and result.
6. Confirm that no token or webhook secret appears in logs, notifications, or error messages.

## Common Mistakes

- **Using the wrong repository:** Check the owner and repository name carefully. Organization repositories and personal repositories can have different permission policies.
- **Granting too many permissions:** Start with read-only access and add only the permissions required by a specific feature.
- **Copying the token incorrectly:** Make sure there are no extra spaces or line breaks when storing it in an environment variable.
- **Forgetting to restart the application:** Many processes do not reload environment variables automatically.
- **Committing secrets:** Check `.gitignore` and secret-scanning alerts. Revoke an exposed token immediately.
- **Using an expired token:** Check the token expiration date and replace it before scheduled jobs begin failing.
- **Testing against the wrong branch:** Confirm the configured default branch matches the repository.
- **Using an HTTP webhook URL:** GitHub integrations should use HTTPS in production.
- **Subscribing to every webhook event:** Select only the events the application handles to reduce noise and processing load.
- **Skipping signature verification:** Validate webhook signatures before accepting event data.
- **Expecting browser-rendered data from an API call:** GitHub API responses and GitHub web pages are different interfaces. Use the API endpoint when the integration expects structured data.

## Troubleshooting

### The connection test returns `401 Unauthorized`

The token is missing, invalid, expired, or being sent in the wrong header. Generate a new token if necessary, update `GITHUB_TOKEN`, restart the application, and run the test again.

### The connection test returns `403 Forbidden`

The token may be valid but lack the required repository permission. Check the token's selected repository and fine-grained permissions. Also check whether the organization requires administrator approval or single sign-on authorization.

### The connection test returns `404 Not Found`

The repository name may be misspelled, or the authenticated token cannot see a private repository. Confirm the `owner/repository` value and verify that the token has access to that exact repository.

### The application says that `GITHUB_TOKEN` is not set

Confirm that the variable is defined in the same shell, container, service, or deployment environment used to start the application. Check the variable name for spelling and restart the process after adding it.

### Webhook deliveries fail with `404`

Confirm that the webhook URL is correct and that the application's route is enabled. Check reverse-proxy routing and make sure the public URL maps to the service that handles GitHub webhooks.

### Webhook deliveries fail with `401` or `403`

The application may be rejecting the webhook secret or signature. Confirm that the configured secret matches GitHub exactly and that the application computes the signature from the raw request body.

### GitHub shows a timeout for webhook deliveries

The endpoint is not responding quickly enough or is unreachable. Verify DNS, firewall, TLS certificate, and reverse-proxy settings. Return a quick success response and process lengthy work asynchronously when possible.

### The application receives duplicate events

GitHub may retry deliveries when it does not receive a successful response. Store and check the delivery ID, such as `X-GitHub-Delivery`, so the application can process each delivery idempotently.

### API rate limits are exceeded

Reduce unnecessary requests, cache stable repository data, and inspect the `X-RateLimit-Remaining` and `X-RateLimit-Reset` response headers. Use an authenticated integration with the minimum required scope and schedule bulk work responsibly.

### A scheduled job stopped working after several weeks

The token may have expired or been revoked. Check the token status, create a replacement with the same minimum permissions, update the secret store, restart the application, and test the connection again.

## Completion Checklist

- [ ] The correct GitHub repository is selected.
- [ ] The token or GitHub App has only the required permissions.
- [ ] Secrets are stored outside source control.
- [ ] The application has been restarted after configuration changes.
- [ ] A read-only connection test succeeds.
- [ ] A normal application workflow succeeds.
- [ ] Webhook signatures are verified, if webhooks are enabled.
- [ ] GitHub webhook delivery logs show successful responses.
- [ ] Application logs do not contain secrets.
