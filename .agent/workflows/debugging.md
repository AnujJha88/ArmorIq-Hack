---
description: Systematic debugging workflow for identifying and fixing bugs efficiently
---

# Debugging Workflow

## The Debugging Mindset

1. **Don't panic** - Bugs are expected; systematic approach beats frustration
2. **Read the error** - Error messages often tell you exactly what's wrong
3. **Reproduce first** - Can't fix what you can't reproduce
4. **Isolate the problem** - Narrow down the scope systematically
5. **One change at a time** - Changing multiple things makes debugging harder

---

## Step 1: Understand the Problem

### Gather Information
```markdown
- [ ] What is the expected behavior?
- [ ] What is the actual behavior?
- [ ] When did it start happening?
- [ ] What changed recently?
- [ ] Is it reproducible? (Always / Sometimes / Rarely)
- [ ] Does it happen in all environments?
```

### Read the Error Message Carefully
```python
# Example error:
# Traceback (most recent call last):
#   File "main.py", line 42, in process_data     <-- Location
#     result = data['key']                        <-- Exact line
# KeyError: 'key'                                 <-- Error type & cause

# What this tells us:
# - File: main.py
# - Line: 42
# - Function: process_data
# - Issue: Trying to access 'key' that doesn't exist
```

---

## Step 2: Reproduce the Bug

### Create Minimal Reproduction
```python
# Bad: "It crashes somewhere in my 1000-line script"
# Good: Isolate to smallest possible case

# Minimal test case
def test_reproduce_bug():
    """Minimal case that reproduces the issue"""
    data = {'other_key': 'value'}  # Missing 'key'
    result = data['key']  # This crashes
```

### Document Reproduction Steps
```markdown
1. Start with fresh database
2. Create user with email "test@test.com"
3. Try to login with same email but uppercase "TEST@test.com"
4. Bug: Login fails when it should succeed (case-insensitive)
```

---

## Step 3: Isolate the Problem

### Binary Search Debugging
```python
# Comment out half the code
# If bug disappears: bug is in commented half
# If bug persists: bug is in uncommented half
# Repeat until you find the exact line

def complex_function():
    step_1()  
    step_2()  
    # --- Bug somewhere below? ---
    step_3()  # <-- Add breakpoint or print here
    step_4()  
    step_5()  
```

### Print Debugging (Quick & Dirty)
```python
def process_data(data):
    print(f"DEBUG: data type = {type(data)}")
    print(f"DEBUG: data keys = {data.keys() if hasattr(data, 'keys') else 'N/A'}")
    print(f"DEBUG: data = {data}")  # Be careful with large data!
    
    # More targeted
    print(f"DEBUG: 'key' in data = {'key' in data}")
    
    result = data['key']
    print(f"DEBUG: reached after data['key']")  # Did we get here?
    
    return result
```

### Logging (Better for Production)
```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def process_data(data):
    logger.debug(f"Processing data with keys: {list(data.keys())}")
    
    if 'key' not in data:
        logger.error(f"Missing 'key' in data. Available: {list(data.keys())}")
        raise KeyError("Required key 'key' not found")
    
    logger.info(f"Successfully processed data")
    return data['key']
```

---

## Step 4: Use Debugger (When Prints Aren't Enough)

### Python Debugger (pdb)
```python
# Method 1: Breakpoint in code
def problematic_function():
    x = compute_something()
    breakpoint()  # Execution pauses here (Python 3.7+)
    y = process(x)  # Step through this
    return y

# Method 2: Run with debugger
# python -m pdb script.py

# Method 3: Post-mortem debugging (after crash)
# python -m pdb -c continue script.py
```

### PDB Commands
```
n (next)     - Execute next line
s (step)     - Step into function
c (continue) - Continue to next breakpoint
p expr       - Print expression
pp expr      - Pretty-print expression
l (list)     - Show current location
w (where)    - Show stack trace
u (up)       - Go up one stack frame
d (down)     - Go down one stack frame
q (quit)     - Quit debugger
```

### VS Code Debugging
```json
// .vscode/launch.json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Current File",
            "type": "python",
            "request": "launch",
            "program": "${file}",
            "console": "integratedTerminal",
            "justMyCode": false  // Step into library code
        }
    ]
}
```

---

## Step 5: Common Bug Patterns

### Off-by-One Errors
```python
# Bug: Index out of range
for i in range(len(arr)):
    print(arr[i], arr[i+1])  # Fails on last iteration!

# Fix:
for i in range(len(arr) - 1):
    print(arr[i], arr[i+1])
```

### None/Null Checks
```python
# Bug: AttributeError: 'NoneType' has no attribute 'xyz'
result = get_user(id)
print(result.name)  # Crashes if user not found

# Fix:
result = get_user(id)
if result is None:
    raise ValueError(f"User {id} not found")
print(result.name)
```

### Mutable Default Arguments
```python
# Bug: List shared across calls!
def add_item(item, items=[]):
    items.append(item)
    return items

add_item(1)  # [1]
add_item(2)  # [1, 2] - Bug! Expected [2]

# Fix:
def add_item(item, items=None):
    if items is None:
        items = []
    items.append(item)
    return items
```

### Type Confusion
```python
# Bug: Comparing string to int
user_input = input("Enter age: ")  # Returns string "25"
if user_input > 18:  # TypeError or wrong comparison!
    print("Adult")

# Fix:
user_input = int(input("Enter age: "))
if user_input > 18:
    print("Adult")
```

### Shallow vs Deep Copy
```python
import copy

# Bug: Modifying copy affects original
original = [1, [2, 3]]
shallow = original.copy()
shallow[1].append(4)
print(original)  # [1, [2, 3, 4]] - Bug!

# Fix:
deep = copy.deepcopy(original)
deep[1].append(4)
print(original)  # [1, [2, 3]] - Original unchanged
```

### Async/Await Issues
```python
# Bug: Forgot to await
async def fetch_data():
    result = fetch_from_api()  # Missing await!
    return result  # Returns coroutine, not data

# Fix:
async def fetch_data():
    result = await fetch_from_api()
    return result
```

---

## Step 6: Verify the Fix

### Write a Test
```python
def test_process_data_missing_key():
    """Regression test for the bug we just fixed"""
    data = {'other_key': 'value'}
    
    with pytest.raises(KeyError):
        process_data(data)
    
    # Or if we added a default:
    result = process_data(data)
    assert result == 'default_value'
```

### Check Edge Cases
```python
# After fixing, test edge cases:
def test_edge_cases():
    assert process_data({}) == 'default'           # Empty
    assert process_data({'key': ''}) == ''         # Empty string
    assert process_data({'key': None}) is None     # None value
    assert process_data({'key': 0}) == 0           # Falsy value
```

---

## Debugging Specific Scenarios

### Memory Issues
```python
# Track memory usage
import tracemalloc

tracemalloc.start()
# ... your code ...
snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')
for stat in top_stats[:10]:
    print(stat)
```

### Performance Issues
```python
import cProfile
import pstats

# Profile code
cProfile.run('main()', 'output.prof')

# Analyze results
stats = pstats.Stats('output.prof')
stats.sort_stats('cumulative')
stats.print_stats(20)
```

### API/Network Issues
```python
# Log all requests
import requests
import logging

logging.basicConfig(level=logging.DEBUG)
logging.getLogger('urllib3').setLevel(logging.DEBUG)

# Now all HTTP requests are logged
response = requests.get('https://api.example.com')
```

### Database Issues
```python
# SQLAlchemy query logging
import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.DEBUG)

# See actual SQL being executed
```

---

## Debugging Checklist

```markdown
- [ ] Can I reproduce the bug consistently?
- [ ] Do I understand the error message?
- [ ] Have I checked recent changes (git diff)?
- [ ] Have I isolated the minimum code that fails?
- [ ] Have I checked input data/types?
- [ ] Have I verified my assumptions with prints/debugger?
- [ ] Have I searched for similar issues (Stack Overflow, GitHub)?
- [ ] Have I written a test that catches this bug?
- [ ] Does the fix break anything else?
```

---

## When You're Stuck

1. **Take a break** - Fresh eyes often spot the issue
2. **Rubber duck debugging** - Explain the problem out loud
3. **Ask for help** - Another perspective helps
4. **Search the error** - Someone probably hit this before
5. **Read the docs** - The behavior might be documented
6. **Check assumptions** - Print/verify everything you "know" is true
