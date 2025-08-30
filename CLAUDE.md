# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a learning project which use FastMCP to connect Playwright MCP and learn how to use FastMCP API with OpenAI API.

## Development Environment

- **Python Version**: Requires Python 3.12+
- **Package Manager**: Uses `uv` for dependency management and virtual environment
- **Project Structure**: Standard Python package with `pyproject.toml` configuration

## Essential Commands

### Environment Setup
```bash
# Install dependencies and set up virtual environment
uv install

# Activate virtual environment (if needed manually)
source .venv/bin/activate
```

### Development Tools
```bash
# Run tests
uv run pytest

# Format code
uv run black .

# Lint code
uv run ruff check .

# Fix linting issues
uv run ruff check --fix .
```

## Dependencies and Architecture

### Core Dependencies
- **OpenAI API**: Primary LLM integration (`openai>=1.0.0`)
- **MCP Components**: 
  - `fastmcp>=2.0.0` - MCP framework
- **Data Processing**: `pydantic>=2.0.0` for data validation, `markdown>=3.5.0` for content processing
- **Async/HTTP**: `aiohttp>=3.8.0` for async HTTP operations
- **CLI**: `rich>=13.0.0` for enhanced terminal output

### Project Structure
- Package source code is expected in `src/` directory (configured in `pyproject.toml`)

## Project Implementation

### Current Implementation Status
The project successfully implements:

1. **MCP Client** (`src/mcp_client.py`):
   - FastMCP-based wrapper for connecting to MCP servers
   - Async context manager support
   - Methods: `ping()`, `list_tools()`, `call_tool()`
   - Successfully connects to Playwright MCP server with 21 browser automation tools

2. **LLM Client** (`src/llm_client.py`):
   - OpenAI API integration with async support
   - Environment variable support for `OPENAI_API_KEY` and `OPENAI_BASE_URL`
   - Tool calling capability for MCP integration
   - Configurable model selection (default: `deepseek/deepseek-chat-v3.1:free`)

3. **Demo Integration** (`main.py`):
   - MCP connection testing and tool discovery
   - LLM + MCP tool calling integration
   - Automatic conversion of MCP tools to OpenAI function format

### Usage

```bash
# Run the main demo
uv run python main.py

# Set environment variables for LLM integration
export OPENAI_API_KEY="your-api-key"
export OPENAI_BASE_URL="https://your-base-url"  # optional
```

### Available Playwright Tools
The connected MCP server provides 21 browser automation tools including:
- `browser_navigate`, `browser_click`, `browser_type`
- `browser_take_screenshot`, `browser_snapshot`
- `browser_fill_form`, `browser_file_upload`
- `browser_evaluate`, `browser_wait_for`
- And more for comprehensive web automation

## MCP Server Configuration
- **Playwright MCP Server**: `http://localhost:8931/mcp`
- **Connection**: HTTP/SSE transport via FastMCP
- **Status**: ✅ Connected and tested

## Notes for Development
- Configuration uses modern Python packaging standards with `pyproject.toml`
- Use FastMCP Python API to connect HTTP MCP servers
- LLM client supports custom base URLs for alternative OpenAI-compatible APIs