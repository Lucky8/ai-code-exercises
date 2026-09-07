# OpenAPI Specification Guide

## Overview

This directory contains complete OpenAPI 3.0 specifications for the User Registration API endpoint. OpenAPI (formerly known as Swagger) is an industry-standard specification format for describing REST APIs.

## Files Included

### 1. **openapi.yaml**
   - YAML format specification
   - Human-readable and commonly used for documentation
   - Best for version control and direct editing

### 2. **openapi.json**
   - JSON format specification
   - Machine-parsable format
   - Compatible with most API tools and platforms

## What's Included in These Specifications

✅ **Endpoint Definitions**
- HTTP method and path: `POST /api/users/register`
- Operation ID for code generation
- Detailed descriptions

✅ **Request Parameters & Schemas**
- Request body schema with all required fields
- Field types, descriptions, and constraints
- Multiple example requests

✅ **Response Schemas**
- Success response (201 Created)
- Error responses (400, 409, 500)
- Detailed field descriptions
- Multiple response examples

✅ **Error Handling**
- All error scenarios documented
- Error schemas with examples
- HTTP status codes with descriptions

✅ **Server Configuration**
- Production server URL
- Development/localhost server URL

## How to Use These Specifications

### 1. **Interactive API Documentation (Swagger UI)**

Convert the OpenAPI spec to interactive documentation:

```bash
# Install Swagger UI locally or use the online editor
# Online: https://editor.swagger.io

# Simply paste the content of openapi.yaml or openapi.json
# into the Swagger Editor for interactive documentation
```

**Benefits:**
- Visualize all endpoints
- Try requests directly from the UI
- Auto-generated client/server code
- Real-time validation

### 2. **API Client Generation**

Generate API clients automatically from the specification:

```bash
# Using OpenAPI Generator
openapi-generator-cli generate \
  -i openapi.yaml \
  -g python \
  -o ./generated-client

# Supports: Python, Java, JavaScript, Go, Ruby, C#, etc.
```

### 3. **Server Code Generation**

Generate server stubs from the specification:

```bash
# Generate Python Flask server
openapi-generator-cli generate \
  -i openapi.yaml \
  -g python-flask \
  -o ./generated-server
```

### 4. **API Documentation Portals**

Publish to documentation platforms:

- **ReDoc** (https://redoc.ly): Beautiful auto-generated docs
- **SwaggerHub** (https://swagger.io): Hosted API documentation
- **MkDocs** with OpenAPI plugin
- **Postman**: Import for testing

### 5. **Validation & Linting**

Validate your specification:

```bash
# Using Spectacle
spectacle openapi.yaml

# Using OpenAPI Validator
openapi-validator openapi.json

# Using Swagger CLI
swagger validate openapi.yaml
```

### 6. **Testing with Postman**

1. Open Postman
2. Click "Import"
3. Select "Link" or "File"
4. Paste the URL or select the JSON file
5. Collections are automatically created with all endpoints and examples

### 7. **CI/CD Integration**

Include specification validation in your build pipeline:

```yaml
# GitHub Actions example
- name: Validate OpenAPI Spec
  uses: actions/setup-node@v2
  run: |
    npm install -g @apidevtools/swagger-cli
    swagger-cli validate openapi.yaml
```

## Schema Components

### Request Schema: `RegistrationRequest`
```yaml
- username (string, required): Desired username
- email (string, required): Email address (must be unique)
- password (string, required): Minimum 8 characters
```

### Response Schema: `UserResponse`
```yaml
- id (integer): User ID
- username (string): Registered username
- email (string): Registered email
- created_at (string, ISO 8601): Creation timestamp
- role (string): User role (user/admin/moderator)
```

### Error Schemas
- `MissingFieldError`: Missing required field
- `InvalidEmailError`: Email format invalid
- `WeakPasswordError`: Password too weak
- `UsernameTakenError`: Username exists
- `EmailExistsError`: Email already registered
- `ServerError`: Internal server error

## Status Codes

| Code | Description | Schema |
|------|-------------|--------|
| 201 | User created successfully | `RegistrationSuccessResponse` |
| 400 | Validation failed | Various error schemas |
| 409 | Resource conflict | Username/Email exists errors |
| 500 | Server error | `ServerError` |

## Validation Rules (from Schema)

- **Username**: 1-255 characters, must be unique
- **Email**: Valid email format, must be unique, normalized to lowercase
- **Password**: 8-255 characters, case-sensitive

## Servers Configured

```yaml
Production:  https://api.example.com
Development: http://localhost:5000
```

Update the server URLs in the specification to match your actual deployment.

## Security Schemes

The specification includes `bearerAuth` scheme for documentation purposes:
- Type: HTTP Bearer Token (JWT)
- Note: Not required for the registration endpoint
- Used for authenticated endpoints in your API

## Integration Examples

### Python with `requests`
```python
import requests
import json

data = {
    "username": "john_doe",
    "email": "john@example.com",
    "password": "SecurePassword123"
}

response = requests.post(
    'https://api.example.com/api/users/register',
    json=data,
    headers={'Content-Type': 'application/json'}
)

print(response.status_code)
print(response.json())
```

### JavaScript with `fetch`
```javascript
const data = {
    username: 'john_doe',
    email: 'john@example.com',
    password: 'SecurePassword123'
};

fetch('https://api.example.com/api/users/register', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify(data)
})
.then(response => response.json())
.then(data => console.log(data));
```

### cURL
```bash
curl -X POST https://api.example.com/api/users/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "SecurePassword123"
  }'
```

## Converting Between YAML and JSON

**YAML to JSON:**
```bash
# Using Python
python3 -c "import yaml, json; print(json.dumps(yaml.safe_load(open('openapi.yaml'))))"

# Using online converter
# https://www.yamltojson.com/
```

**JSON to YAML:**
```bash
# Using Python
python3 -c "import yaml, json; print(yaml.dump(json.load(open('openapi.json'))))"
```

## Viewing the Specification

### Online Editors
- **Swagger Editor**: https://editor.swagger.io
- **OpenAPI Editor**: https://openapi.tools/
- **Stoplight Studio**: https://stoplight.io/

### Local Viewers
- **Spectacle**: `npm install -g spectacle-docs`
- **ReDoc CLI**: `npm install -g redoc-cli`

## Maintenance & Updates

When updating your API:

1. Update the OpenAPI specification
2. Update the version number in `info.version`
3. Validate the new specification
4. Regenerate client/server code if needed
5. Update API documentation portals
6. Regenerate SDKs from the spec

## Best Practices

✅ Keep specifications in sync with actual implementation
✅ Use meaningful descriptions for all fields
✅ Include realistic examples for all responses
✅ Document all error scenarios
✅ Maintain version history
✅ Use meaningful operation IDs for code generation
✅ Include security schemes even if optional
✅ Add external documentation links

## Tools & Resources

| Tool | Purpose | Link |
|------|---------|------|
| Swagger UI | Interactive API documentation | https://swagger.io/tools/swagger-ui/ |
| Swagger Editor | Online specification editor | https://editor.swagger.io |
| ReDoc | Beautiful API documentation | https://redoc.ly |
| Postman | API testing and development | https://www.postman.com |
| OpenAPI Generator | Code generation from specs | https://openapi-generator.tech |
| Swagger CLI | Validation and bundling | https://github.com/swagger-api/swagger-js |
| Spectacle | API documentation generator | https://github.com/sourcey/spectacle |

## Troubleshooting

**Issue: "Invalid OpenAPI document"**
- Validate syntax using Swagger Editor or CLI tools
- Check YAML/JSON formatting
- Ensure all `$ref` references are valid

**Issue: "Schema validation failed"**
- Verify all required fields are present
- Check field types match schema definitions
- Ensure examples match their schemas

**Issue: "Can't generate code"**
- Verify OpenAPI version (3.0.0)
- Check operationId is provided
- Ensure schemas are complete

## Related Documentation

- [OpenAPI 3.0 Specification](https://spec.openapis.org/oas/v3.0.3)
- [OpenAPI Examples](https://github.com/OAI/OpenAPI-Specification/tree/master/examples)
- [API Design Best Practices](https://swagger.io/resources/articles/best-practices-in-api-design/)

---

**Last Updated:** 2026-09-07
**API Version:** 1.0.0
**OpenAPI Version:** 3.0.0
