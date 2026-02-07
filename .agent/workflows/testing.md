---
description: Testing workflow with pytest including unit tests, fixtures, and mocking
---

# Testing Workflow with Pytest

## Setup

// turbo
```powershell
pip install pytest pytest-cov pytest-mock
```

## Project Structure
```
tests/
├── __init__.py
├── conftest.py          # Shared fixtures
├── unit/
│   └── test_models.py
└── integration/
    └── test_api.py
```

---

## Writing Tests

### Basic Test
```python
import pytest
from myapp.calculator import add, divide

def test_add_positive_numbers():
    assert add(2, 3) == 5

def test_divide_by_zero_raises_error():
    with pytest.raises(ValueError):
        divide(10, 0)
```

### Parametrized Tests
```python
@pytest.mark.parametrize("a,b,expected", [
    (1, 2, 3),
    (0, 0, 0),
    (-1, 1, 0),
])
def test_add_parametrized(a, b, expected):
    assert add(a, b) == expected
```

---

## Fixtures

```python
# conftest.py
import pytest

@pytest.fixture
def sample_user():
    return {"id": 1, "name": "Test User"}

@pytest.fixture
def db_session():
    conn = create_connection()
    yield conn  # Test runs here
    conn.close()  # Cleanup

# Use in test
def test_user(sample_user):
    assert sample_user["id"] == 1
```

---

## Mocking

```python
from unittest.mock import patch, Mock

@patch('myapp.services.external_api')
def test_with_mock(mock_api):
    mock_api.return_value = {"status": "ok"}
    result = my_service()
    assert result["status"] == "ok"
```

---

## Running Tests

// turbo
```powershell
pytest -v                    # Verbose
pytest --cov=src             # With coverage
pytest -k "user"             # Match pattern
pytest -m "not slow"         # Skip slow tests
```
