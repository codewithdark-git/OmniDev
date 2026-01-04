# 🚀 OmniDev

> **Your Multi-Model AI Development Assistant - Free, Intelligent, Autonomous**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Status: In Development](https://img.shields.io/badge/status-in%20development-orange.svg)]()

OmniDev is an intelligent CLI-based AI coding assistant that brings the power of multiple AI models to your terminal - **for free**. It combines autonomous operation, strategic planning, and smart model selection to help you code faster and better.

---

## ✨ What OmniDev Does

OmniDev is your AI pair programmer that:

- 🤖 **Creates, edits, and manages files** automatically based on natural language instructions
- 🧠 **Plans complex changes** before executing them, showing you the full impact
- 🎯 **Intelligently selects the best AI model** for each task (coding, debugging, refactoring, testing)
- 🔄 **Maintains dynamic project context** - automatically includes relevant files without manual selection
- 💰 **Starts completely free** using gpt4free, with optional premium API upgrades
- 🛡️ **Keeps your code safe** with automatic backups and Git integration
- 🎨 **Modern Rich CLI** with colorful UI, slash commands, and interactive mode
- 🤝 **CrewAI Agent System** for intelligent orchestration of all internal operations
- ⚙️ **Project-specific configuration** with `.env` file support for API keys

---

## 🎮 Four Operational Modes

### 1. **Agent Mode** 🤖
Full autonomy - tell it what you want, and it handles everything automatically.

```bash
$ omnidev "Build a REST API for user authentication with JWT"

→ Creating project structure...
✓ Created 5 files
✓ Implemented authentication logic
✓ Generated tests
✓ All tests passing

Done! Your API is ready.
```

### 2. **Planning Mode** 📋
Strategic approach - shows you the plan first, then executes with your approval.

```bash
$ omnidev --mode planning "Refactor authentication to use OAuth2"

→ Creating refactoring plan...

PLAN: OAuth2 Migration
├─ Phase 1: Setup (5 files, ~15 min)
├─ Phase 2: Core migration (4 files, ~20 min)  
├─ Phase 3: Integration (3 files, ~10 min)
└─ Phase 4: Testing (6 files, ~10 min)

Proceed? (yes/no/modify):
```

### 3. **Auto-Select Mode** 🎯
Smart model routing - automatically picks the best AI model for each task.

```bash
$ omnidev "Fix this performance issue"

🎯 Selected: Claude Sonnet 4 (best for optimization)
→ Analyzing code...
→ Found bottleneck in database query
✓ Applied optimization (35x faster)
```

### 4. **Manual Mode** 🎮
Full control - you approve every step and choose which AI model to use.

```bash
$ omnidev --mode manual "Create a new component"

Which model? (gpt-4o/claude/deepseek): gpt-4o
Should I create new file? (yes/no): yes
Filename: components/UserProfile.tsx
✓ Created
```

---

## 🚀 Quick Start

### Installation

**For Users:**
```bash
# Install OmniDev
pip install omnidev

# First-time setup (configure OpenRouter API key for agents)
omnidev setup
```

**For Developers:**
See [README_SETUP.md](README_SETUP.md) for detailed setup instructions using Miniconda and UV package manager.

### OpenRouter API Key Setup (Required for Agents)

OmniDev uses **OpenRouter API keys exclusively for agent operations** (internal orchestration, decision-making, planning, validation). The OpenRouter API is **NOT used** for code generation.

**Quick Setup:**
```bash
omnidev setup
```

This interactive wizard will guide you through:
1. Entering your OpenRouter API key (get it from [openrouter.ai/keys](https://openrouter.ai/keys))
2. Choosing storage location (project `.env` file or system keyring)
3. Verifying the key is saved correctly

**Manual Setup:**
Create a `.env` file in your project root:
```bash
# .env
OMNIDEV_OPENROUTER_API_KEY=your-api-key-here
```

**Important:** Add `.env` to your `.gitignore` to keep your API key secure.

For detailed setup instructions, see [SETUP_OPENROUTER.md](SETUP_OPENROUTER.md).

### Basic Usage

```bash
# Start in your project directory
cd my-project

# Use natural language to code
omnidev "create a Python FastAPI server with authentication"

# Agent mode (full autonomy)
omnidev --mode agent "add user registration endpoint"

# Planning mode (review before execution)
omnidev --mode planning "refactor the database layer"

# Use specific model
omnidev --model gpt-4o "explain how this algorithm works"
```

---

## 🎯 Core Features

### Intelligent File Operations
- **Create** new files with proper structure and conventions
- **Edit** existing files with surgical precision
- **Delete** files safely with confirmation
- **Multi-file coordination** for complex refactoring

### Dynamic Context Management
- Automatically includes relevant files based on your task
- Learns which files you work on together
- Optimizes token usage to fit more context
- Updates context in real-time as you work

### Smart Model Routing
- Analyzes each task and selects the optimal AI model
- Balances quality, speed, and cost automatically
- Falls back gracefully when models are unavailable
- Learns from your feedback to improve selections

### Safety & Reliability
- Automatic backups before any destructive operation
- Git integration with smart commit messages
- Easy rollback with one command
- Validates code before applying changes

---

## 💡 Example Workflows

### Create a New Feature
```bash
$ omnidev "add password reset functionality to the auth system"

→ Planning implementation...
→ Creating email templates...
→ Adding reset token logic...
→ Updating API endpoints...
→ Generating tests...
✓ Feature complete! 8 files modified, 247 lines added
```

### Debug an Issue
```bash
$ omnidev "why is the /users endpoint returning 500 errors?"

🎯 Selected: GPT-4 Turbo (best for debugging)
→ Analyzing error logs...
→ Found: Missing database migration
→ Solution: Run migration 'add_user_email_index'

Apply fix? (yes/no): yes
✓ Migration applied
✓ Tests passing
```

### Refactor Code
```bash
$ omnidev --mode planning "convert this Flask app to FastAPI"

REFACTORING PLAN:
├─ Update dependencies (requirements.txt)
├─ Convert route decorators (12 files)
├─ Update request/response models (8 files)
├─ Migrate database ORM (4 files)
└─ Update tests (15 files)

Estimated time: 2-3 hours
Breaking changes: Yes

Proceed? (yes/no):
```

### Generate Tests
```bash
$ omnidev "write comprehensive tests for the authentication module"

→ Analyzing auth.py...
→ Generating test scenarios...
✓ Created tests/test_auth_happy_path.py (8 tests)
✓ Created tests/test_auth_errors.py (12 tests)
✓ Created tests/test_auth_edge_cases.py (7 tests)

Coverage: 94% → Run tests? (yes/no):
```

---

## 🔧 Configuration

OmniDev works out of the box, but you can customize it:

### OpenRouter API Key (Required for Agents)

The OpenRouter API key is required for agent operations. Set it up using:

```bash
# Interactive setup wizard (recommended)
omnidev setup

# Or manually via CLI
omnidev config add-key openrouter YOUR_OPENROUTER_API_KEY

# Or create .env file in project root
echo "OMNIDEV_OPENROUTER_API_KEY=your-key-here" > .env
```

**Note:** OpenRouter is used exclusively for agent orchestration, NOT for code generation.

### Global Configuration
```bash
# Set your preferred default model
omnidev config set default-model claude-sonnet-4

# Add your API keys (optional, for premium models)
omnidev config add-key openai YOUR_API_KEY
omnidev config add-key anthropic YOUR_API_KEY

# Set daily budget limit
omnidev config set budget 5.00
```

### Project Configuration
Create `.omnidev.yaml` in your project root:

```yaml
project_name: "My API Project"
default_mode: agent

models:
  preferred: claude-sonnet-4
  fallback: gpt4free

context:
  always_include:
    - "config/*.py"
    - "models/*.py"
  exclude:
    - "*.log"
    - "node_modules/*"
```

---

## 🌟 Why OmniDev?

### vs. Claude Code
- ✅ **Free tier available** (Claude Code requires paid API)
- ✅ **Multiple AI models** (not locked to one provider)
- ✅ **Smart model selection** (uses best model for each task)
- ✅ **Planning mode** (see changes before they happen)

### vs. Cursor
- ✅ **CLI-first design** (works with any editor)
- ✅ **Autonomous modes** (less manual intervention)
- ✅ **Free to start** (no subscription required)
- ✅ **Open source** (customize and extend)

### vs. GitHub Copilot
- ✅ **Full file operations** (not just autocomplete)
- ✅ **Project-wide context** (understands your entire codebase)
- ✅ **Multi-model support** (not limited to OpenAI)
- ✅ **Intelligent planning** (thinks before acting)

---

## 🛠️ Technology

**Built with:**
- Python 3.10+ for core logic
- [gpt4free](https://github.com/xtekky/gpt4free) for free AI model access
- Official APIs: OpenAI, Anthropic, Google (optional)
- Rich CLI for beautiful terminal interface
- GitPython for version control integration

**Supported AI Models:**
- GPT-4o, GPT-4 Turbo, GPT-4o-mini (OpenAI)
- Claude Sonnet 4, Claude Opus 4 (Anthropic)
- Gemini 2.0 Flash, Gemini 2.5 Pro (Google)
- DeepSeek, o1, o3 (via gpt4free)
- And many more through gpt4free providers

**Supported Languages & Frameworks:**
- Python (Django, FastAPI, Flask)
- JavaScript/TypeScript (React, Node.js, Express, Next.js)
- Go, Rust, Java, C#, PHP, Ruby
- And more...

---

## 📋 Requirements

- Python 3.10 or higher
- Git (for version control features)
- Internet connection (for AI models)

**Required for Agents:**
- OpenRouter API key (for agent orchestration) - Configure with `omnidev setup`

**Optional (for premium models):**
- OpenAI API key (for GPT-4, GPT-4o)
- Anthropic API key (for Claude models)
- Google API key (for Gemini models)

---

## 🗺️ Roadmap

### ✅ Current (v0.1 - MVP)
- Agent, Planning, Auto-Select, and Manual modes
- File create, edit, delete operations
- GPT4Free integration
- Basic context management
- Git integration

### 🚧 In Progress (v0.2)
- Web search integration
- Documentation fetching
- Enhanced context scoring
- Official API integrations (OpenAI, Anthropic)

### 📅 Coming Soon (v0.3+)
- MCP server support
- IDE integrations (VS Code, JetBrains)
- Advanced testing capabilities
- Performance profiling
- Team collaboration features

---

## 🤝 Contributing

We welcome contributions! Whether it's:
- 🐛 Bug reports
- 💡 Feature suggestions
- 📝 Documentation improvements
- 🔧 Code contributions

Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- [gpt4free](https://github.com/xtekky/gpt4free) for providing free access to AI models
- [g4f-working](https://github.com/Free-AI-Things/g4f-working) for tracking working providers
- The open-source community for inspiration and support

---

## 💬 Community & Support

- **GitHub Issues**: [Report bugs or request features](https://github.com/yourusername/omnidev/issues)
- **Discussions**: [Ask questions and share ideas](https://github.com/yourusername/omnidev/discussions)
- **Discord**: [Join our community](#) (coming soon)
- **Twitter**: [@omnidev_ai](#) (coming soon)

---

## ⚡ Quick Examples

```bash
# Create a complete web application
omnidev "build a todo app with React frontend and FastAPI backend"

# Debug production issues
omnidev "analyze why the server is slow and fix it"

# Refactor legacy code
omnidev --mode planning "modernize this codebase to use async/await"

# Learn from your code
omnidev "explain how the authentication flow works"

# Generate documentation
omnidev "create API documentation for all endpoints"

# Add new features
omnidev "add user profile editing with avatar upload"
```

---

<div align="center">

**Made with ❤️ for developers who want AI assistance without the premium price tag**

[⭐ Star us on GitHub](https://github.com/yourusername/omnidev) • [📖 Read the Docs](#) • [🐦 Follow Updates](#)

</div>