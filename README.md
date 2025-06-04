# 🔒 Bandit Security Scanner MCP

MCP (Model Context Protocol) wrapper for Bandit - a specialized Python security linter that analyzes AST and detects common security issues.

## 🌟 Features

- **Python Code Security Analysis**: Vulnerability detection through AST analysis
- **MCP Support**: Integration with any MCP clients
- **Web Interface**: Convenient Gradio interface for manual testing
- **Baseline Management**: Create and compare with baseline files
- **Profile Scanning**: Use specialized security profiles
- **Flexible Configuration**: Customize severity and confidence levels

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run Servers

```bash
# Run Bandit MCP server
python app.py

# Run Detect Secrets MCP server
python detect_secrets_mcp.py
```

The servers will be available at:
- **Bandit Web Interface**: `http://localhost:7860`
- **Bandit MCP Server**: `http://localhost:7860/gradio_api/mcp/sse`
- **Bandit MCP Schema**: `http://localhost:7860/gradio_api/mcp/schema`
- **Detect Secrets Web Interface**: `http://localhost:7861`
- **Detect Secrets MCP Server**: `http://localhost:7861/gradio_api/mcp/sse`
- **Detect Secrets MCP Schema**: `http://localhost:7861/gradio_api/mcp/schema`

## 🔧 Available Tools

### 1. Bandit Tools

#### 1.1 `bandit_scan` - Basic Scanning

Analyzes Python code for security issues.

**Parameters:**
- `code_input`: Python code or path to file/directory
- `scan_type`: "code" (direct code) or "path" (file/directory)
- `severity_level`: "low", "medium", "high"
- `confidence_level`: "low", "medium", "high"  
- `output_format`: "json", "txt"

**Usage Example:**
```python
bandit_scan(
    code_input="eval(user_input)",
    scan_type="code",
    severity_level="medium",
    confidence_level="high"
)
```

#### 1.2 `bandit_baseline` - Baseline Management

Creates baseline file or compares with existing one.

**Parameters:**
- `target_path`: Path to project for analysis
- `baseline_file`: Path to baseline file

#### 1.3 `bandit_profile_scan` - Profile Scanning

Runs scanning using specific security profile.

**Parameters:**
- `target_path`: Path to project
- `profile_name`: "ShellInjection", "SqlInjection", "Crypto", "Subprocess"

### 2. Detect Secrets Tools

#### 2.1 `detect_secrets_scan` - Basic Scanning

Scans code for secrets using detect-secrets.

**Parameters:**
- `code_input`: Code to scan or path to file/directory
- `scan_type`: "code" (direct code) or "path" (file/directory)
- `base64_limit`: Entropy limit for base64 strings (0.0-8.0)
- `hex_limit`: Entropy limit for hex strings (0.0-8.0)
- `exclude_lines`: Regex pattern for lines to exclude
- `exclude_files`: Regex pattern for files to exclude
- `exclude_secrets`: Regex pattern for secrets to exclude
- `word_list`: Path to word list file
- `output_format`: "json" or "txt"

**Usage Example:**
```python
detect_secrets_scan(
    code_input="API_KEY = 'sk_live_51H1h2K3L4M5N6O7P8Q9R0S1T2U3V4W5X6Y7Z8'",
    scan_type="code",
    base64_limit=4.5,
    hex_limit=3.0
)
```

#### 2.2 `detect_secrets_baseline` - Baseline Management

Creates or updates a baseline file for detect-secrets.

**Parameters:**
- `target_path`: Path to code for analysis
- `baseline_file`: Path to baseline file
- `base64_limit`: Entropy limit for base64 strings
- `hex_limit`: Entropy limit for hex strings

#### 2.3 `detect_secrets_audit` - Baseline Audit

Audits a detect-secrets baseline file.

**Parameters:**
- `baseline_file`: Path to baseline file
- `show_stats`: Show statistics
- `show_report`: Show report
- `only_real`: Only show real secrets
- `only_false`: Only show false positives

## 🎯 What Bandit Detects

- **Insecure Functions**: `exec()`, `eval()`, `compile()`
- **Hardcoded Passwords**: Hard-coded secrets in code
- **Insecure Serialization**: Using `pickle` without validation
- **SQL Injections**: Unsafe SQL query formation
- **Shell Injections**: Command execution with `shell=True`
- **SSL Issues**: Missing certificate verification
- **Weak Encryption Algorithms**: Using outdated methods
- **File Permission Issues**: Insecure file permissions

## 🔍 What Detect Secrets Detects

- **API Keys**: Various service API keys
- **Passwords**: High entropy strings that look like passwords
- **Private Keys**: RSA, SSH, and other private keys
- **OAuth Tokens**: Various OAuth tokens
- **AWS Keys**: AWS access and secret keys
- **GitHub Tokens**: GitHub personal access tokens
- **Slack Tokens**: Slack API tokens
- **Stripe Keys**: Stripe API keys
- **And More**: Many other types of secrets

## 🧪 Vulnerable Code Examples

### 1. Using eval()
```python
user_input = "print('hello')"
eval(user_input)  # B307: Use of possibly insecure function
```

### 2. Hardcoded password
```python
password = "secret123"  # B105: Possible hardcoded password
```

### 3. Insecure subprocess
```python
import subprocess
subprocess.call("ls -la", shell=True)  # B602: subprocess call with shell=True
```

### 4. Using pickle
```python
import pickle
data = pickle.loads(user_data)  # B301: Pickle usage
```

### 5. API Key
```python
API_KEY = "sk_live_51H1h2K3L4M5N6O7P8Q9R0S1T2U3V4W5X6Y7Z8"  # Detect Secrets: API Key
```

### 6. Private Key
```python
private_key = "-----BEGIN RSA PRIVATE KEY-----\nMIIEpAIBAAKCAQEA..."  # Detect Secrets: Private Key
```

## 🌐 MCP Client Integration

### Configuration for Cursor IDE

```json
{
  "mcpServers": {
    "bandit-security": {
      "command": "npx",
      "args": [
        "-y", 
        "mcp-remote", 
        "http://localhost:7860/gradio_api/mcp/sse",
        "--transport", 
        "sse-only"
      ]
    },
    "detect-secrets": {
      "command": "npx",
      "args": [
        "-y", 
        "mcp-remote", 
        "http://localhost:7861/gradio_api/mcp/sse",
        "--transport", 
        "sse-only"
      ]
    }
  }
}
```

### Configuration for Other MCP Clients

```json
{
  "servers": [
    {
      "name": "Bandit Security Scanner",
      "transport": {
        "type": "sse",
        "url": "http://localhost:7860/gradio_api/mcp/sse"
      }
    },
    {
      "name": "Detect Secrets Scanner",
      "transport": {
        "type": "sse",
        "url": "http://localhost:7861/gradio_api/mcp/sse"
      }
    }
  ]
}
```

## 📊 Results Format

### JSON Scan Result
```json
{
  "success": true,
  "results": {
    "errors": [],
    "generated_at": "2024-01-01T12:00:00Z",
    "metrics": {
      "_totals": {
        "CONFIDENCE.HIGH": 1,
        "SEVERITY.MEDIUM": 1,
        "loc": 10,
        "nosec": 0
      }
    },
    "results": [
      {
        "code": "eval(user_input)",
        "filename": "/tmp/example.py",
        "issue_confidence": "HIGH",
        "issue_severity": "MEDIUM",
        "issue_text": "Use of possibly insecure function - consider using safer alternatives.",
        "line_number": 2,
        "line_range": [2],
        "test_id": "B307",
        "test_name": "blacklist"
      }
    ]
  }
}
```

## 🚀 Deploy on Hugging Face Spaces

1. Create a new Space on Hugging Face
2. Choose Gradio SDK
3. Upload `app.py`, `detect_secrets_mcp.py` and `requirements.txt` files
4. MCP servers will be available at:
   - Bandit: `https://YOUR_USERNAME-bandit-mcp.hf.space/gradio_api/mcp/sse`
   - Detect Secrets: `https://YOUR_USERNAME-detect-secrets-mcp.hf.space/gradio_api/mcp/sse`

## 🤝 AI Agent Integration

This MCP server can be integrated with any AI agents supporting MCP:

- **Claude Desktop**: Through MCP configuration
- **Cursor IDE**: Through MCP server settings  
- **Tiny Agents**: Through JavaScript or Python clients
- **Custom Agents**: Through HTTP+SSE or stdio

## 📖 Additional Resources

- [Bandit Documentation](https://bandit.readthedocs.io/)
- [Detect Secrets Documentation](https://github.com/Yelp/detect-secrets)
- [MCP Specification](https://spec.modelcontextprotocol.io/)
- [Gradio MCP Integration](https://gradio.app/guides/mcp-integration/)

---

**Note**: Both Bandit and Detect Secrets are static analyzers and cannot detect all types of vulnerabilities. Use them as part of a comprehensive security strategy. 