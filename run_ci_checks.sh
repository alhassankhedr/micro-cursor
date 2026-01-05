#!/bin/bash
# Run the same checks that GitHub CI runs locally
# This helps catch errors before pushing to GitHub

set -e  # Exit on any error

echo "=== Running CI checks locally ==="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo -e "${RED}Error: pyproject.toml not found. Please run this script from the project root.${NC}"
    exit 1
fi

# 1. Run ruff check
echo "1. Running ruff check..."
if ruff check .; then
    echo -e "${GREEN}✓ ruff check passed${NC}"
else
    echo -e "${RED}✗ ruff check failed${NC}"
    exit 1
fi
echo ""

# 2. Run ruff format check
echo "2. Running ruff format check..."
if ruff format --check .; then
    echo -e "${GREEN}✓ ruff format check passed${NC}"
else
    echo -e "${RED}✗ ruff format check failed (run 'ruff format .' to fix)${NC}"
    exit 1
fi
echo ""

# 3. Run tests
echo "3. Running tests..."
if pytest tests/ -v; then
    echo -e "${GREEN}✓ tests passed${NC}"
else
    echo -e "${RED}✗ tests failed${NC}"
    exit 1
fi
echo ""

# 4. Test CLI help
echo "4. Testing CLI help..."
if python -m micro_cursor --help > /dev/null 2>&1; then
    echo -e "${GREEN}✓ CLI help works${NC}"
else
    echo -e "${RED}✗ CLI help failed${NC}"
    exit 1
fi
echo ""

echo -e "${GREEN}=== All CI checks passed! ==="
echo "You're ready to push to GitHub.${NC}"

