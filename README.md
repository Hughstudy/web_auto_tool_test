# MCP Task Orchestrator - Playwright Integration

This project demonstrates how to use **FastMCP** to create an intelligent web automation system powered by **Playwright MCP** and **LLM control** (using DeepSeek Chat).

## Features

- 🎭 **Playwright MCP Integration**: Direct control of web browser automation
- 🤖 **LLM-Powered Automation**: Use AI to intelligently analyze pages and plan actions
- 🔧 **FastMCP Framework**: Modern MCP server implementation
- 🎯 **Multiple Operation Modes**: Basic scripting, LLM control, and interactive demos
- 📝 **Smart Form Filling**: AI identifies and fills forms automatically
- 📊 **Data Extraction**: Structured data extraction guided by AI
- 🔍 **Intelligent Navigation**: Goal-oriented web browsing

## Prerequisites

1. **Node.js** (for Playwright MCP server)
2. **Python 3.12+**
3. **uv** package manager
4. **OpenAI-compatible API** (configured for DeepSeek)

## Setup

### 1. Install Dependencies

```bash
# Install Python dependencies
uv install

# Install Playwright MCP (globally)
npm install -g @playwright/mcp@latest
```

### 2. Environment Configuration

Create a `.env` file with your AI model configuration:

```env
OPENAI_API_KEY=your_deepseek_api_key
OPENAI_BASE_URL=https://api.deepseek.com
```

### 3. MCP Server Configuration

Add this to your MCP client configuration:

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp@latest"]
    }
  }
}
```

## Usage

### Quick Start

### Option 1: Simple Demo (No API Keys Required)

See the concepts in action with simulated Playwright actions:

```bash
python simple_demo.py
```

### Option 2: Full Demo (Requires API Setup)

Run demonstrations with real LLM control:

```bash
# First set up your API keys in .env file
cp .env.example .env
# Edit .env with your DeepSeek API credentials

python main.py demo
```

### Available Modes

1. **Simple Demo** - Works without API keys:
   ```bash
   python simple_demo.py
   ```

2. **Demo Mode** - Full LLM capabilities (requires API setup):
   ```bash
   python main.py demo
   ```

3. **Interactive Mode** - Custom tasks:
   ```bash
   python main.py interactive
   ```

4. **LLM Server** - Run as MCP server:
   ```bash
   python main.py llm
   ```

5. **Basic Server** - Simple Playwright wrapper:
   ```bash
   python main.py basic
   ```

## Example Capabilities

### 🔍 Intelligent Web Search
```python
# LLM analyzes Google, performs search, and clicks first result
await controller.analyze_page_and_act(
    url="https://www.google.com",
    goal="Search for 'FastMCP Python library' and click on the first result",
    context="Looking for FastMCP documentation"
)
```

### 📝 Smart Form Filling
```python
# LLM identifies form fields and fills them appropriately
form_data = {
    "name": "John Doe",
    "email": "john@example.com",
    "subject": "MCP Integration Question"
}

await controller.intelligent_form_filling(
    url="https://example.com/contact",
    form_data=form_data,
    submit=False
)
```

### 📊 Data Extraction
```python
# LLM extracts structured data from any webpage
await controller.extract_structured_data(
    url="https://github.com/microsoft/playwright",
    data_description="Extract repo name, stars, description, and recent commits"
)
```

## How It Works

### 1. **Playwright MCP Integration**
- Connects to `@playwright/mcp` server
- Provides browser automation tools (navigate, click, fill, screenshot)
- Handles all browser management automatically

### 2. **LLM Intelligence Layer**
- **DeepSeek Chat v3.1** analyzes web page content
- Creates action plans to achieve specified goals
- Identifies form fields and UI elements intelligently
- Adapts to different website structures

### 3. **FastMCP Framework**
- Modern MCP server implementation
- Async/await support for better performance
- Tool registration and management
- Error handling and logging

## Project Structure

```
├── src/
│   ├── mcp_playwright_server.py      # Basic Playwright MCP wrapper
│   ├── llm_playwright_controller.py  # LLM-powered automation
│   ├── llm_demo.py                   # Demonstration scripts
│   └── example_usage.py              # Usage examples
├── main.py                           # Main entry point
├── pyproject.toml                    # Python project config
└── README.md                         # This file
```

## Development

### Running Tests
```bash
uv run pytest
```

### Code Formatting
```bash
uv run black .
```

### Linting
```bash
uv run ruff check .
```

## Key Components

### 1. PlaywrightMCPServer
Basic wrapper around Playwright MCP providing:
- `navigate_to_page()` - Navigate to URLs
- `take_screenshot()` - Capture page screenshots
- `extract_text()` - Get page text content
- `click_element()` - Click UI elements
- `fill_form_field()` - Fill form inputs

### 2. LLMPlaywrightController
AI-powered automation providing:
- `analyze_page_and_act()` - Goal-oriented automation
- `intelligent_form_filling()` - Smart form completion
- `extract_structured_data()` - AI-guided data extraction

### 3. Interactive Demo System
- Real-time task specification
- Multiple demonstration scenarios
- Progress tracking and error handling

## Common Use Cases

1. **Automated Testing**: AI-driven test case execution
2. **Data Scraping**: Intelligent content extraction
3. **Form Automation**: Smart form filling for repetitive tasks
4. **Website Monitoring**: Automated page analysis and reporting
5. **Research Automation**: Gathering information from multiple sources

## Troubleshooting

### MCP Connection Issues
- Ensure `@playwright/mcp` is installed globally
- Check MCP server configuration in your client
- Verify Node.js version compatibility

### API Configuration
- Confirm `OPENAI_API_KEY` and `OPENAI_BASE_URL` are set correctly
- Test API connectivity independently
- Check DeepSeek API rate limits

### Browser Automation Issues
- Playwright may need to install browsers: `npx playwright install`
- Some sites block automation - use delays and realistic interactions
- Check for CAPTCHA or bot detection mechanisms

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure code formatting with `black` and `ruff`
5. Submit a pull request

## License

This project is for educational purposes. Please respect website terms of service when using automation tools.