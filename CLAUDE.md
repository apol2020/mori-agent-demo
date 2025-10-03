# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Commands

### Environment Setup
```bash
make setup           # Full development environment setup (includes pre-commit hooks)
make install         # Install production dependencies only
make install-dev     # Install development dependencies only
cp .env.example .env # Set up environment configuration
```

### Running the Application
```bash
make run             # Run Streamlit app (production mode)
make dev-server      # Run with auto-reload for development

# Direct run with specific settings
PYTHONPATH=. streamlit run src/app.py --server.headless=true --server.port=8501
```

### Testing
```bash
make test            # Run all tests
make test-unit       # Run unit tests only (tests/unit/)
make test-integration # Run integration tests only (tests/integration/)
make test-ui         # Run UI tests only (tests/ui/)

# Run specific test file
PYTHONPATH=. pytest tests/unit/core/test_data_service.py -v

# Run tests with coverage
PYTHONPATH=. pytest --cov=src --cov-report=html
```

### Code Quality
```bash
make lint            # Run Ruff linting
make format          # Auto-format code (Ruff + Black + isort)
make type-check      # Run mypy type checking
make check-all       # Run all quality checks (lint + type-check + test)
```

### Utilities
```bash
make clean           # Clean cache and temporary files
make init-db         # Initialize database (if using database features)
```

## Architecture Overview

This project follows **Clean Architecture** principles with strict layer separation:

### Layer Structure
```
src/
├── ui/                     # UI Layer (Streamlit-specific)
├── core/                   # Core Business Logic Layer
├── infrastructure/         # Infrastructure Layer
├── config/                 # Configuration
└── utils/                  # Shared utilities
```

### Dependency Flow
```
UI Layer → Core Layer → Infrastructure Layer
```

**Critical**: Dependencies only flow inward. Core layer is framework-agnostic and contains no UI or infrastructure imports.

### Key Architectural Patterns

1. **Agent Abstraction**: Base agent pattern in `core/agents/base_agent.py`, implemented by `ChatAgent` in `core/agents/chat_agent.py`
2. **LLM Factory Pattern**: Multi-LLM support through `infrastructure/llm/llm_factory.py` (supports Claude Sonnet 4.5, GPT-5, GPT-5 mini)
3. **Tool Registry Pattern**: Tools abstracted through base class (`core/tools/base.py`) with central registry (`core/tools/registry.py`)
4. **Service Layer**: Business logic uses async/await pattern
5. **Models**: Domain entities and data structures in `core/models/` (ChatMessage, MessageRole, etc.)
6. **Output Normalization**: `core/common/output_handler.py` provides consistent response formatting across LLM providers

### Streamlit Application Structure

- **Entry Point**: `src/app.py` - main application with page routing
- **Page Routing**: Pages selected via sidebar (see `ui/components/sidebar.py`), routed in main()
- **Main Page**: `ui/pages/agent_chat.py` - agent chat interface with streaming support
- **Components**: Reusable UI components in `ui/components/` (chat_interface.py, sidebar.py)
- **Layouts**: Page layouts and templates in `ui/layouts/base.py`
- **UI Config**: Tool display configuration in `ui/config/tool_display_config.py`

## Testing Architecture

Tests follow the same structure as source code:
- **Unit Tests**: `tests/unit/` - Test business logic in isolation
- **Integration Tests**: `tests/integration/` - Test layer interactions
- **UI Tests**: `tests/ui/` - Test Streamlit components

### Test Markers
- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.ui` - UI tests
- `@pytest.mark.asyncio` - Async tests

## Development Workflow

1. **Environment Setup**: Run `make setup` for first-time setup
2. **Code Changes**: Follow existing patterns in each layer
3. **Quality Checks**: Run `make check-all` before committing
4. **Pre-commit Hooks**: Automatically run on commit (Black, isort, Ruff, mypy)

## Code Quality Configuration

- **Line Length**: 120 characters (configured in pyproject.toml)
- **Type Checking**: Strict mypy configuration with type annotations required
- **Formatting**: Black + isort with consistent import organization
- **Linting**: Ruff with comprehensive rule set including security checks

## Environment Configuration

Copy `.env.example` to `.env` and configure:
- **Required API Keys**:
  - `ANTHROPIC_API_KEY` - For Claude models
  - `OPENAI_API_KEY` - For GPT models
- Application settings (APP_NAME, DEBUG)
- Model configuration (ANTHROPIC_MODEL, ANTHROPIC_TEMPERATURE, ANTHROPIC_MAX_TOKENS)
- Streamlit configuration (PAGE_TITLE, PAGE_ICON, LAYOUT)
- Logging (LOG_LEVEL, LOG_FORMAT)

## Important Notes

- **PYTHONPATH**: Most commands require `PYTHONPATH=.` to resolve imports correctly
- **Async Services**: Core services use async/await - remember to await service calls
- **Type Annotations**: Required for all functions and methods (enforced by mypy with relaxed settings)
- **Import Organization**: Follow isort configuration for consistent import grouping
- **LangChain Integration**:
  - LangGraph adapter in `infrastructure/llm/langchain_adapter.py`
  - Uses LangChain Hub prompt (`hwchase17/openai-tools-agent`) with ReAct agent pattern
  - Session-based message history via `ChatMessageHistory`
- **Multi-LLM Support**:
  - Factory pattern in `infrastructure/llm/llm_factory.py`
  - Direct Anthropic integration via `anthropic_client.py`
  - Unified interface across Claude/OpenAI models
- **Tool Development**:
  - New tools extend `BaseTool` (from `core/tools/base.py`)
  - Implement `execute()` method (sync or async)
  - Register in `ToolRegistry` for automatic discovery
  - Examples: `GetCurrentTimeTool`, `MultiplyTool`
- **Streaming Support**:
  - Token-level streaming for agent responses
  - Tool input streaming for both Claude and OpenAI APIs
  - Real-time tool execution status display
- **Session Management**: Streamlit session state manages conversation history per user session
