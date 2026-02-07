---
description: Set up a new Python project with virtual environment, dependencies, and best practices
---

# Python Project Setup Workflow

## 1. Create Project Structure

```
project_name/
├── src/
│   └── project_name/
│       ├── __init__.py
│       └── main.py
├── tests/
│   ├── __init__.py
│   └── test_main.py
├── data/               # For data files (gitignored)
├── notebooks/          # Jupyter notebooks
├── scripts/            # Utility scripts
├── .gitignore
├── README.md
├── requirements.txt
├── pyproject.toml
└── .env.example
```

## 2. Create Virtual Environment

// turbo
```powershell
python -m venv .venv
```

## 3. Activate Virtual Environment

```powershell
.\.venv\Scripts\Activate.ps1
```

## 4. Create pyproject.toml (Modern Python)

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "project_name"
version = "0.1.0"
description = "Project description"
readme = "README.md"
requires-python = ">=3.10"
dependencies = []

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
    "black>=23.0",
    "ruff>=0.1",
    "mypy>=1.0",
    "pre-commit>=3.0",
]

[tool.black]
line-length = 100
target-version = ['py310']

[tool.ruff]
line-length = 100
select = ["E", "F", "I", "N", "W", "UP"]

[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true
```

## 5. Create .gitignore

// turbo
```powershell
# Create comprehensive Python .gitignore
```

Essential entries:
```
# Virtual environments
.venv/
venv/
ENV/

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
dist/
*.egg-info/

# IDE
.idea/
.vscode/
*.swp
*.swo

# Environment
.env
.env.local

# Data
data/
*.csv
*.parquet
*.pkl

# Jupyter
.ipynb_checkpoints/

# Testing
.pytest_cache/
.coverage
htmlcov/

# Misc
*.log
.DS_Store
Thumbs.db
```

## 6. Install Dependencies

// turbo
```powershell
pip install -e ".[dev]"
```

## 7. Initialize Git Repository

```powershell
git init
git add .
git commit -m "Initial project setup"
```

## 8. Set Up Pre-commit Hooks (Optional but Recommended)

Create `.pre-commit-config.yaml`:
```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files

  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.9
    hooks:
      - id: ruff
        args: [--fix]
```

// turbo
```powershell
pre-commit install
```

## 9. Create README.md Template

```markdown
# Project Name

Brief description of what this project does.

## Installation

\`\`\`bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1  # Windows
pip install -e ".[dev]"
\`\`\`

## Usage

\`\`\`python
from project_name import main
# Example usage
\`\`\`

## Development

Run tests:
\`\`\`bash
pytest tests/ -v
\`\`\`

## License

MIT
```

## Verification Checklist

- [ ] Virtual environment created and activated
- [ ] Dependencies installed successfully
- [ ] Git repository initialized
- [ ] Project structure follows best practices
- [ ] README provides clear setup instructions
