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

### 2. Run Server

```bash
python app.py
```

The server will be available at:
- **Web Interface**: `http://localhost:7860`
- **MCP Server**: `http://localhost:7860/gradio_api/mcp/sse`
- **MCP Schema**: `http://localhost:7860/gradio_api/mcp/schema`

## 🔧 Available Tools

### 1. `bandit_scan` - Basic Scanning

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

### 2. `bandit_baseline` - Baseline Management

Creates baseline file or compares with existing one.

**Parameters:**
- `target_path`: Path to project for analysis
- `baseline_file`: Path to baseline file

### 3. `bandit_profile_scan` - Profile Scanning

Runs scanning using specific security profile.

**Parameters:**
- `target_path`: Path to project
- `profile_name`: "ShellInjection", "SqlInjection", "Crypto", "Subprocess"

## 🎯 What Bandit Detects

- **Insecure Functions**: `exec()`, `eval()`, `compile()`
- **Hardcoded Passwords**: Hard-coded secrets in code
- **Insecure Serialization**: Using `pickle` without validation
- **SQL Injections**: Unsafe SQL query formation
- **Shell Injections**: Command execution with `shell=True`
- **SSL Issues**: Missing certificate verification
- **Weak Encryption Algorithms**: Using outdated methods
- **File Permission Issues**: Insecure file permissions

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
3. Upload `app.py` and `requirements.txt` files
4. MCP server will be available at: `https://YOUR_USERNAME-bandit-mcp.hf.space/gradio_api/mcp/sse`

## 🤝 AI Agent Integration

This MCP server can be integrated with any AI agents supporting MCP:

- **Claude Desktop**: Through MCP configuration
- **Cursor IDE**: Through MCP server settings  
- **Tiny Agents**: Through JavaScript or Python clients
- **Custom Agents**: Through HTTP+SSE or stdio

## 📖 Additional Resources

- [Bandit Documentation](https://bandit.readthedocs.io/)
- [MCP Specification](https://spec.modelcontextprotocol.io/)
- [Gradio MCP Integration](https://gradio.app/guides/mcp-integration/)

---

**Note**: Bandit is a static analyzer and cannot detect all types of vulnerabilities. Use it as part of a comprehensive security strategy. 