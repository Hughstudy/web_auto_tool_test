# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**MCP Task Orchestrator** is an intelligent task automation system that combines Large Language Models (LLMs) with Model Context Protocol (MCP) tools for complex web-based task execution. The project demonstrates a clean architecture pattern with smart progress evaluation and automatic tool execution.

## Development Environment

- **Python Version**: Requires Python 3.12+
- **Package Manager**: Uses `uv` for dependency management and virtual environment
- **Project Structure**: Clean architecture with separation of concerns

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

### Running the Application
```bash
# Run the interactive terminal interface (RECOMMENDED)
uv run python interaction.py

# Run the original orchestrator demo
uv run python main.py

# Set required environment variables
export OPENAI_API_KEY="your-api-key"
export OPENAI_BASE_URL="https://your-base-url"  # optional
```

### Interactive Terminal Interface
The system now includes a sophisticated terminal interface (`interaction.py`) with the following features:

#### Commands Available:
- `/model` - List all available models from OpenAI API (320+ models)
- `/model <name>` - Switch to a different model (e.g., `/model gpt-4o`)
- `/clear` - Clear conversation history and reset context
- `/quit` - Exit the program cleanly
- `Ctrl+C/ESC` - Interrupt running tasks immediately

#### Key Features:
- **Dynamic Model Discovery**: Automatically fetches and displays all available models from OpenAI API
- **Smart Task Interruption**: Press Ctrl+C during task execution to stop immediately
- **Conversation Reset**: New prompts automatically interrupt running tasks and reset iterations
- **Rich Terminal UI**: Professional interface with colored output, tables, and progress indicators
- **Graceful Error Handling**: Robust error recovery and user feedback

## Dependencies and Architecture

### Core Dependencies
- **OpenAI API**: Primary LLM integration (`openai>=1.0.0`)
- **MCP Framework**: `fastmcp>=2.0.0` for MCP server communication
- **Data Validation**: `pydantic>=2.0.0` for structured data handling
- **Async Operations**: `aiohttp>=3.8.0` for HTTP operations
- **CLI Enhancement**: `rich>=13.0.0` for terminal output
- **Configuration**: `python-dotenv>=1.0.0` for environment management

### Architecture Overview
```
# Interactive Mode (RECOMMENDED)
interaction.py → TerminalInterface → Instruction + ResourceManager
                          ↓                ↓              ↓
                 InteractiveOrchestrator  Commands    LLMClient + MCPClient
                          ↓                              ↓
                 BaseOrchestrator                 MessageSystem
                 (common logic)              (conversation management)

# Original Demo Mode  
main.py → ResourceManager → TaskOrchestrator → LLMClient + MCPClient
               ↓                    ↓                    ↓
          Client Management   BaseOrchestrator      MessageSystem
          (resource handling) (common logic)   (conversation management)
```

## Project Implementation

### Core Components

1. **TerminalInterface** (`interaction.py`):
   - Main terminal interface coordinating user interactions
   - Task execution management with interruption support
   - Integration with Instruction and ResourceManager classes
   - Professional user experience with rich terminal UI

2. **Instruction** (`src/instruction.py`):
   - Handles all command processing and instruction display
   - Command routing for `/model`, `/clear`, `/quit` commands
   - Welcome message and help text generation
   - Clean separation of UI logic from business logic

3. **ResourceManager** (`src/resource_manager.py`):
   - Centralizes LLM client, MCP client, and orchestrator management
   - Handles client initialization and connection monitoring
   - Model switching and conversation history management
   - MCP connection liveness monitoring and recovery

4. **BaseOrchestrator** (`src/orchestrator/base_orchestrator.py`):
   - Common orchestration logic shared by all orchestrator types
   - Progress evaluation and JSON-based assessment
   - Tool preparation and iteration execution
   - Clean separation of concerns for maintainability

5. **InteractiveOrchestrator** (`src/orchestrator/interactive_orchestrator.py`):
   - Inherits from BaseOrchestrator with interrupt support
   - Async cancellation handling for responsive UI
   - Progress evaluation with user control
   - Specialized for terminal interaction use cases

6. **TaskOrchestrator** (`src/orchestrator/task_orchestrator.py`):
   - Inherits from BaseOrchestrator for batch processing
   - Simple task execution without interruption
   - Ideal for automated/scripted workflows
   - Minimal overhead for straightforward tasks

7. **LLMClient** (`src/llm_client.py`):
   - OpenAI API integration with automatic tool calling
   - Single-cycle tool execution with retry mechanisms
   - Support for multiple OpenAI-compatible APIs
   - Model: `openai/gpt-5-nano` (configurable)

8. **MCPClient** (`src/mcp_client.py`):
   - FastMCP wrapper for MCP server communication
   - Async context manager support
   - Tool discovery and execution capabilities
   - Connects to Playwright MCP server

9. **MessageSystem** (`src/message_system.py`):
   - Centralized conversation management
   - OpenAI format conversion
   - Tool call tracking and result management
   - Conversation history and summaries

### Current Capabilities

The system demonstrates complex task orchestration by:
- **Multi-step Planning**: Breaking complex tasks into executable steps
- **Progress Evaluation**: Smart assessment of task completion status
- **Tool Integration**: Seamless MCP tool calling through OpenAI function calling
- **Error Handling**: Retry mechanisms and graceful failure recovery
- **Conversation Management**: Proper message formatting and history tracking

### Example Task Flow
```
User Request → TaskOrchestrator → Progress Evaluation → Tool Selection → 
LLM with Tools → MCP Tool Execution → Progress Check → Iteration/Completion
```

## MCP Server Configuration

- **Server URL**: `http://localhost:8931/mcp`
- **Transport**: HTTP/SSE via FastMCP
- **Tools Available**: 21+ Playwright browser automation tools
- **Connection Status**: Async context managed

### Available Tool Categories
- **Navigation**: `browser_navigate`, `browser_go_back`, `browser_refresh`
- **Interaction**: `browser_click`, `browser_type`, `browser_fill_form`
- **Content**: `browser_take_screenshot`, `browser_snapshot`, `browser_extract`
- **Automation**: `browser_wait_for`, `browser_evaluate`, `browser_file_upload`

## Development Guidelines

### Code Style
- Follow existing patterns and conventions
- Use async/await for all I/O operations
- Implement proper error handling with retries
- Use type hints and docstrings

### Testing Approach
- Run tests with `uv run pytest`
- Test MCP connectivity before running orchestrator
- Validate LLM API configuration

### Architecture Principles
- **Separation of Concerns**: Each component has a single responsibility
- **Async First**: All operations are designed for async execution
- **Clean Interfaces**: Well-defined APIs between components
- **Error Resilience**: Proper exception handling and recovery

## Environment Variables

Required:
- `OPENAI_API_KEY`: Your OpenAI API key

Optional:
- `OPENAI_BASE_URL`: Custom API endpoint for OpenAI-compatible services

## Notes for Development

- The system uses modern Python packaging with `pyproject.toml`
- FastMCP provides the bridge between MCP servers and Python clients
- TaskOrchestrator manages the complete lifecycle of complex tasks
- MessageSystem ensures proper conversation state management
- All components support async context management for clean resource handling