# 🚀 OmniDev

> **Your Multi-Model AI Development Assistant - Free, Intelligent, Autonomous**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Status: In Development](https://img.shields.io/badge/status-in%20development-orange.svg)]()

OmniDev is an intelligent CLI-based AI coding assistant that brings the power of multiple AI models to your terminal - **with a free tier**. It combines autonomous operation, strategic planning, and smart model selection to help you code faster and better.

---

## ✨ What OmniDev Does

OmniDev is your AI pair programmer that:

- 🤖 **Creates, edits, and manages files** automatically based on natural language instructions
- 🧠 **Plans complex changes** before executing them, showing you the full impact
- 🎯 **Intelligently selects the best AI model** for each task (coding, debugging, refactoring, testing)
- 🔄 **Maintains dynamic project context** - automatically includes relevant files without manual selection
- 💰 **Free tier available** using Groq (30 requests/minute), with optional premium API upgrades
- 🛡️ **Keeps your code safe** with automatic backups and Git integration
- 🎨 **Modern Rich CLI** with colorful UI, loading spinners, slash commands, and interactive REPL mode
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
pip install git+https://github.com/codewithdark-git/OmniDev.git

# Run interactive setup wizard
omnidev -i
```

**For Developers:**
See [README_SETUP.md](README_SETUP.md) for detailed setup instructions using Miniconda and UV package manager.

### Interactive Mode (Recommended)

Start OmniDev in interactive REPL mode for a chat-like experience:

```bash
omnidev -i
# or
omnidev --interactive
```

This launches an interactive shell with:
- 💬 Chat-style interface
- 🔄 Loading spinners while waiting for responses
- ⚙️ In-REPL setup wizard (`/setup`)
- 🎨 Beautiful terminal UI with panels and colors
- 📜 Command history and auto-suggestions
- 🔧 Slash commands for quick actions

**Available Slash Commands:**
| Command | Description |
|---------|-------------|
| `/help` | Show all available commands |
| `/setup` | Run full setup wizard |
| `/provider` | Change AI provider |
| `/model` | Change AI model |
| `/mode` | Change operational mode |
| `/status` | Show current configuration |
| `/clear` | Clear the screen |
| `/exit` | Exit the REPL |

### Provider Setup

OmniDev supports multiple AI providers. On first run, you'll be guided through setup:

**Supported Providers:**
| Provider | Free Tier | API Key Required |
|----------|-----------|------------------|
| **Groq** | ✅ Yes (30 req/min) | ✅ Yes (free at [console.groq.com](https://console.groq.com)) |
| OpenAI | ❌ No | ✅ Yes |
| Anthropic | ❌ No | ✅ Yes |
| Google | ❌ No | ✅ Yes |
| OpenRouter | ✅ Yes | ✅ Yes |

**Quick Setup:**
```bash
# Interactive setup (recommended)
omnidev -i
# Then type: /setup

# Or run setup directly
omnidev --setup
```

**Manual Setup:**
Create a `.env` file in your project root:
```bash
# .env
GROQ_API_KEY=your-groq-api-key-here
# or
OPENAI_API_KEY=your-openai-api-key-here
```

**Important:** Add `.env` to your `.gitignore` to keep your API keys secure.

### Basic Usage

```bash
# Start interactive mode (recommended)
omnidev -i

# Run a single query
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
- No automatic fallback - shows clear errors when provider fails
- Respects your provider/model selection

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

### Interactive Session
```bash
$ omnidev -i

╭────────────────────────────────────────────╮
│  Welcome to OmniDev Interactive Mode       │
│                                            │
│    ⚡ Provider: groq                       │
│    🤖 Model:    llama-3.3-70b-versatile    │
│    📋 Mode:     agent                      │
│                                            │
│    Type /help for commands!                │
╰────────────────────────────────────────────╯

❯ tell me about the current project structure

💭 Thinking with llama-3.3-70b-versatile via Groq (Free)...

╭────────────────────────────────────────────╮
│  The project follows a modular structure   │
│  with clear separation of concerns...      │
╰────────────────────────────────────────────╯
```

---

## 🔧 Configuration

OmniDev works out of the box, but you can customize it:

### Interactive Setup (Recommended)
```bash
# Start interactive mode and run setup
omnidev -i
❯ /setup
```

### Global Configuration
```bash
# Set your preferred default model
omnidev config set default-model llama-3.3-70b-versatile

# Add your API keys
omnidev config add-key groq YOUR_API_KEY
omnidev config add-key openai YOUR_API_KEY
omnidev config add-key anthropic YOUR_API_KEY
```

### Project Configuration
Create `.omnidev.yaml` in your project root:

```yaml
project_name: "My API Project"

mode:
  default_mode: agent

models:
  preferred: llama-3.3-70b-versatile
  fallback: groq

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
- ✅ **Free tier available** (Groq offers 30 req/min free)
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
- [Groq](https://groq.com) for fast, free AI inference
- Official APIs: OpenAI, Anthropic, Google, OpenRouter (optional)
- [Rich](https://github.com/Textualize/rich) for beautiful terminal interface
- [prompt_toolkit](https://github.com/prompt-toolkit/python-prompt-toolkit) for interactive REPL
- GitPython for version control integration
- CrewAI for agent orchestration

**Supported AI Models:**
- LLaMA 3.3 70B, LLaMA 3.1 8B, Mixtral (Groq - Free)
- GPT-4o, GPT-4 Turbo, GPT-4o-mini (OpenAI)
- Claude Sonnet 4, Claude Opus 4 (Anthropic)
- Gemini 2.0 Flash, Gemini 2.5 Pro (Google)
- Many more through OpenRouter

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

**Required:**
- API key from at least one provider (Groq is free!)

**Optional (for premium models):**
- OpenAI API key (for GPT-4, GPT-4o)
- Anthropic API key (for Claude models)
- Google API key (for Gemini models)
- OpenRouter API key (for access to many models)

---

## 🗺️ Roadmap

### ✅ Current (v0.1 - MVP)
- Agent, Planning, Auto-Select, and Manual modes
- File create, edit, delete operations
- Groq integration (free tier)
- Interactive REPL mode with loading spinners
- Basic context management
- Git integration
- In-REPL setup wizard

### 🚧 In Progress (v0.2)
- Web search integration
- Documentation fetching
- Enhanced context scoring
- Streaming responses

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

- [Groq](https://groq.com) for providing fast, free AI inference
- [Rich](https://github.com/Textualize/rich) for the beautiful terminal UI
- [CrewAI](https://github.com/joaomdmoura/crewAI) for agent orchestration
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
# Start interactive mode (recommended)
omnidev -i

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
