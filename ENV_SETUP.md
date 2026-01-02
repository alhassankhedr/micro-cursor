# Environment Variable Setup Guide

## Overview

micro-cursor reads LLM configuration from **environment variables**. These are **NOT stored in any code files** - you must set them yourself.

## Where Configuration is Read

The code reads environment variables using Python's `os.getenv()` function in `micro_cursor/llm.py`:

- **Line 79**: `os.getenv("OPENAI_API_KEY", "")`
- **Line 80**: `os.getenv("OPENAI_MODEL", "gpt-4o-mini")`
- **Line 136**: `os.getenv("GEMINI_API_KEY", "")`
- **Line 137**: `os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")`
- **Line 190**: `os.getenv("LLM_PROVIDER", "openai")`

## How to Set Environment Variables

### Option 1: Set in Your Shell (Temporary)

**macOS/Linux:**
```bash
export LLM_PROVIDER=openai
export OPENAI_API_KEY=sk-your-key-here
export OPENAI_MODEL=gpt-4o-mini
```

**Windows (PowerShell):**
```powershell
$env:LLM_PROVIDER="openai"
$env:OPENAI_API_KEY="sk-your-key-here"
$env:OPENAI_MODEL="gpt-4o-mini"
```

**Windows (CMD):**
```cmd
set LLM_PROVIDER=openai
set OPENAI_API_KEY=sk-your-key-here
set OPENAI_MODEL=gpt-4o-mini
```

### Option 2: Create a `.env` File (Recommended)

Create a `.env` file in the project root:

```bash
# .env file
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o-mini
```

Then load it before running:
```bash
# macOS/Linux
export $(cat .env | xargs)

# Or use python-dotenv (install: pip install python-dotenv)
# Then add to your code: from dotenv import load_dotenv; load_dotenv()
```

**Note:** Add `.env` to `.gitignore` to avoid committing secrets!

### Option 3: Set in Your Shell Profile (Permanent)

**macOS/Linux** - Add to `~/.bashrc` or `~/.zshrc`:
```bash
export OPENAI_API_KEY=sk-your-key-here
export LLM_PROVIDER=openai
```

**Windows** - Set via System Properties → Environment Variables

### Option 4: Set When Running Command

```bash
# macOS/Linux
OPENAI_API_KEY=sk-your-key-here python -m micro_cursor run --goal "test"

# Windows PowerShell
$env:OPENAI_API_KEY="sk-your-key-here"; python -m micro_cursor run --goal "test"
```

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LLM_PROVIDER` | No | `"openai"` | Provider: `"openai"` or `"gemini"` |
| `OPENAI_API_KEY` | Yes (if using OpenAI) | - | Your OpenAI API key |
| `OPENAI_MODEL` | No | `"gpt-4o-mini"` | OpenAI model name |
| `GEMINI_API_KEY` | Yes (if using Gemini) | - | Your Gemini API key |
| `GEMINI_MODEL` | No | `"gemini-2.0-flash-exp"` | Gemini model name |

## Security Best Practices

1. **Never commit API keys to git** - Add `.env` to `.gitignore`
2. **Use environment variables** - Don't hardcode keys in code
3. **Rotate keys regularly** - If a key is exposed, regenerate it
4. **Use different keys for dev/prod** - Don't share keys across environments

## Verification

Check if variables are set:
```bash
# macOS/Linux
echo $OPENAI_API_KEY

# Windows PowerShell
echo $env:OPENAI_API_KEY
```

Test the import (should work even without keys):
```bash
python -c "from micro_cursor import llm; print('Import successful')"
```

Test getting a client (will error if keys missing):
```bash
python -c "from micro_cursor.llm import get_llm_client; get_llm_client()"
```

