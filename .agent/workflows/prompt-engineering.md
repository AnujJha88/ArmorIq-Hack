---
description: Prompt engineering techniques for getting better results from LLMs
---

# Prompt Engineering Techniques

## Core Principles

1. **Be specific** - Vague prompts get vague answers
2. **Provide examples** - Few-shot > zero-shot
3. **Structure output** - Specify format explicitly
4. **Iterate** - Prompting is experimentation

---

## Basic Patterns

### Role Assignment
```
You are an expert Python developer with 15 years of experience.
You write clean, well-documented, production-ready code.
```

### Task + Context + Format
```
Task: Summarize the following article.
Context: This is for a newsletter targeting busy executives.
Format: Bullet points, max 5 points, each under 20 words.

Article: [content]
```

### Step-by-Step Instructions
```
Follow these steps:
1. Read the code carefully
2. Identify any bugs or issues
3. Explain each issue found
4. Provide corrected code
5. Explain your fixes
```

---

## Advanced Techniques

### Chain of Thought (CoT)
```
Solve this problem step by step:

Problem: If a train travels 120 km in 2 hours, then stops for 30 minutes, 
then travels another 90 km in 1.5 hours, what is the average speed for 
the entire journey?

Let's think through this:
1. First, calculate total distance...
2. Then, calculate total time...
3. Finally, divide...
```

### Few-Shot Learning
```
Convert natural language to SQL:

User: Show all users from California
SQL: SELECT * FROM users WHERE state = 'California';

User: Count orders from last month  
SQL: SELECT COUNT(*) FROM orders WHERE created_at >= DATE_SUB(NOW(), INTERVAL 1 MONTH);

User: Find users who haven't ordered anything
SQL:
```

### Self-Consistency
```
Solve this problem 3 different ways, then pick the most reliable answer:

Problem: [complex problem]

Approach 1: ...
Approach 2: ...
Approach 3: ...

Most reliable answer based on consistency: ...
```

---

## Output Control

### JSON Output
```
Respond with valid JSON only. No other text.

Schema:
{
  "summary": "string",
  "sentiment": "positive|negative|neutral",
  "key_points": ["string"],
  "confidence": 0.0-1.0
}
```

### Structured Reasoning
```
Use this format:

<thinking>
Your step-by-step reasoning here
</thinking>

<answer>
Your final answer here
</answer>
```

---

## Avoiding Common Issues

### Reduce Hallucinations
```
Important instructions:
- Only use information explicitly stated in the context
- If you don't know something, say "I don't have enough information"
- Do not make up facts, statistics, or citations
- Distinguish between what's stated vs what you're inferring
```

### Handle Edge Cases
```
If the input is unclear or ambiguous:
1. State what's unclear
2. List possible interpretations
3. Proceed with the most likely interpretation
4. Note any assumptions made
```

---

## Prompt Templates

### Code Review
```
Review this code for:
1. Bugs and errors
2. Security vulnerabilities  
3. Performance issues
4. Code style/readability

For each issue found:
- Line number
- Issue type (bug/security/performance/style)
- Severity (critical/high/medium/low)
- Explanation
- Suggested fix

Code:
```python
{code}
```
```

### Technical Explanation
```
Explain {concept} as if explaining to:
1. A 5-year-old (simple analogy)
2. A college student (technical but accessible)
3. An expert (precise technical details)
```

### Debugging Assistant
```
I'm encountering this error:
{error_message}

Here's my code:
{code}

Please:
1. Explain what's causing the error
2. Show the fix
3. Explain why the fix works
4. Suggest how to prevent similar issues
```

---

## Iteration Strategy

1. **Start simple** → Add complexity as needed
2. **Test edge cases** → Unusual inputs reveal weaknesses  
3. **A/B test prompts** → Compare outputs systematically
4. **Save good prompts** → Build a library
5. **Version control** → Track what works
