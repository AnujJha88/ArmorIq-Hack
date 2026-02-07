---
description: Building AI agents with LLMs including tool use, memory, planning, and multi-agent systems
---

# Agentic AI Development Workflow

## Core Concepts

### What Makes an Agent?
```
┌─────────────────────────────────────────────────────────┐
│                        AGENT                            │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐   │
│  │  LLM    │  │  Tools  │  │ Memory  │  │Planning │   │
│  │ (Brain) │  │(Actions)│  │(Context)│  │(Goals)  │   │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘   │
└─────────────────────────────────────────────────────────┘
```

**Agent = LLM + Tools + Memory + Planning Loop**

---

## Phase 1: Basic Agent Setup

### 1.1 Install Dependencies
// turbo
```powershell
pip install openai anthropic langchain langgraph pydantic
```

### 1.2 Simple ReAct Agent (From Scratch)
```python
import openai
from typing import Callable

class SimpleAgent:
    def __init__(self, tools: dict[str, Callable], model: str = "gpt-4"):
        self.tools = tools
        self.model = model
        self.client = openai.OpenAI()
        
    def _build_system_prompt(self):
        tool_descriptions = "\n".join([
            f"- {name}: {func.__doc__}" 
            for name, func in self.tools.items()
        ])
        
        return f"""You are a helpful AI assistant with access to tools.

Available tools:
{tool_descriptions}

To use a tool, respond with:
TOOL: tool_name
INPUT: tool input

After receiving tool output, continue reasoning or provide final answer.
When done, respond with:
FINAL: your final answer
"""
    
    def run(self, user_query: str, max_steps: int = 10) -> str:
        messages = [
            {"role": "system", "content": self._build_system_prompt()},
            {"role": "user", "content": user_query}
        ]
        
        for step in range(max_steps):
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages
            )
            
            assistant_msg = response.choices[0].message.content
            messages.append({"role": "assistant", "content": assistant_msg})
            
            # Check for final answer
            if "FINAL:" in assistant_msg:
                return assistant_msg.split("FINAL:")[1].strip()
            
            # Check for tool use
            if "TOOL:" in assistant_msg:
                tool_name = assistant_msg.split("TOOL:")[1].split("\n")[0].strip()
                tool_input = assistant_msg.split("INPUT:")[1].strip()
                
                if tool_name in self.tools:
                    result = self.tools[tool_name](tool_input)
                    messages.append({
                        "role": "user", 
                        "content": f"Tool result: {result}"
                    })
        
        return "Max steps reached"


# Define tools
def search_web(query: str) -> str:
    """Search the web for information"""
    # Implement actual search
    return f"Search results for: {query}"

def calculate(expression: str) -> str:
    """Calculate a mathematical expression"""
    return str(eval(expression))

# Create agent
agent = SimpleAgent(tools={
    "search": search_web,
    "calculate": calculate
})

result = agent.run("What is 15% of the population of France?")
```

---

## Phase 2: Tool Design Patterns

### 2.1 Structured Tool Definitions
```python
from pydantic import BaseModel, Field
from typing import Literal

class ToolInput(BaseModel):
    """Base class for tool inputs"""
    pass

class SearchInput(ToolInput):
    query: str = Field(..., description="Search query")
    num_results: int = Field(default=5, description="Number of results")

class FileReadInput(ToolInput):
    path: str = Field(..., description="File path to read")
    
class CodeExecuteInput(ToolInput):
    code: str = Field(..., description="Python code to execute")
    timeout: int = Field(default=30, description="Timeout in seconds")


class Tool:
    name: str
    description: str
    input_schema: type[ToolInput]
    
    def __init__(self, name: str, description: str, input_schema: type[ToolInput]):
        self.name = name
        self.description = description
        self.input_schema = input_schema
    
    def execute(self, input_data: dict) -> str:
        validated = self.input_schema(**input_data)
        return self._run(validated)
    
    def _run(self, input_data: ToolInput) -> str:
        raise NotImplementedError


class SearchTool(Tool):
    def __init__(self):
        super().__init__(
            name="web_search",
            description="Search the web for current information",
            input_schema=SearchInput
        )
    
    def _run(self, input_data: SearchInput) -> str:
        # Actual implementation
        return f"Results for: {input_data.query}"
```

### 2.2 OpenAI Function Calling Format
```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Search the web for information",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function", 
        "function": {
            "name": "run_python",
            "description": "Execute Python code and return output",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Python code to execute"
                    }
                },
                "required": ["code"]
            }
        }
    }
]

response = client.chat.completions.create(
    model="gpt-4",
    messages=messages,
    tools=tools,
    tool_choice="auto"
)
```

---

## Phase 3: Memory Systems

### 3.1 Conversation Memory
```python
from collections import deque

class ConversationMemory:
    def __init__(self, max_messages: int = 20):
        self.messages = deque(maxlen=max_messages)
    
    def add(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})
    
    def get_context(self) -> list[dict]:
        return list(self.messages)
    
    def summarize(self, client) -> str:
        """Summarize old messages to save context"""
        if len(self.messages) < 10:
            return ""
        
        old_msgs = list(self.messages)[:10]
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{
                "role": "user",
                "content": f"Summarize this conversation:\n{old_msgs}"
            }]
        )
        return response.choices[0].message.content
```

### 3.2 Vector Memory (RAG)
```python
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

class VectorMemory:
    def __init__(self, collection_name: str = "agent_memory"):
        self.client = QdrantClient(":memory:")  # or URL
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        self.collection = collection_name
        
        # Create collection
        self.client.create_collection(
            collection_name=self.collection,
            vectors_config={"size": 384, "distance": "Cosine"}
        )
    
    def store(self, text: str, metadata: dict = None):
        vector = self.encoder.encode(text).tolist()
        self.client.upsert(
            collection_name=self.collection,
            points=[{
                "id": hash(text),
                "vector": vector,
                "payload": {"text": text, **(metadata or {})}
            }]
        )
    
    def retrieve(self, query: str, top_k: int = 5) -> list[str]:
        vector = self.encoder.encode(query).tolist()
        results = self.client.search(
            collection_name=self.collection,
            query_vector=vector,
            limit=top_k
        )
        return [r.payload["text"] for r in results]
```

---

## Phase 4: Planning & Reasoning

### 4.1 Chain of Thought
```python
COT_SYSTEM_PROMPT = """
Think step by step before answering.

For each step:
1. State what you're trying to figure out
2. Consider relevant information
3. Reason through the problem
4. Draw a conclusion

After thinking, provide your final answer.
"""
```

### 4.2 Plan-and-Execute Pattern
```python
class PlanExecuteAgent:
    def __init__(self, client, tools):
        self.client = client
        self.tools = tools
    
    def plan(self, goal: str) -> list[str]:
        """Generate a plan to achieve the goal"""
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[{
                "role": "user",
                "content": f"""Create a step-by-step plan to: {goal}
                
Available tools: {list(self.tools.keys())}

Return a numbered list of steps."""
            }]
        )
        # Parse steps from response
        return self._parse_steps(response.choices[0].message.content)
    
    def execute_step(self, step: str, context: str) -> str:
        """Execute a single step"""
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[{
                "role": "system",
                "content": f"Previous context: {context}"
            }, {
                "role": "user", 
                "content": f"Execute this step: {step}"
            }],
            tools=self._format_tools()
        )
        return self._process_response(response)
    
    def run(self, goal: str) -> str:
        plan = self.plan(goal)
        context = ""
        
        for step in plan:
            result = self.execute_step(step, context)
            context += f"\nStep: {step}\nResult: {result}"
        
        return context
```

### 4.3 ReAct Pattern (Reasoning + Acting)
```python
REACT_PROMPT = """
You are an AI assistant that thinks step-by-step.

For each step, use this format:
Thought: [your reasoning about what to do next]
Action: [tool_name]
Action Input: [input to the tool]
Observation: [tool result - will be provided]

... repeat Thought/Action/Observation ...

When you have enough information:
Thought: I now have enough information to answer.
Final Answer: [your final answer]
"""
```

---

## Phase 5: Multi-Agent Systems

### 5.1 Simple Multi-Agent Setup
```python
class Agent:
    def __init__(self, name: str, role: str, client):
        self.name = name
        self.role = role
        self.client = client
    
    def respond(self, message: str, context: list[dict]) -> str:
        messages = [
            {"role": "system", "content": f"You are {self.name}. {self.role}"},
            *context,
            {"role": "user", "content": message}
        ]
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=messages
        )
        return response.choices[0].message.content


class MultiAgentOrchestrator:
    def __init__(self, agents: list[Agent]):
        self.agents = {a.name: a for a in agents}
        self.conversation = []
    
    def run_conversation(self, initial_task: str, max_turns: int = 10):
        current_message = initial_task
        
        for turn in range(max_turns):
            for name, agent in self.agents.items():
                response = agent.respond(current_message, self.conversation)
                self.conversation.append({
                    "role": "assistant",
                    "content": f"[{name}]: {response}"
                })
                current_message = response
                print(f"{name}: {response}\n")


# Example: Researcher + Critic agents
researcher = Agent(
    name="Researcher",
    role="You research topics thoroughly and provide detailed information.",
    client=client
)

critic = Agent(
    name="Critic", 
    role="You critically analyze information and identify gaps or issues.",
    client=client
)

orchestrator = MultiAgentOrchestrator([researcher, critic])
orchestrator.run_conversation("Analyze the pros and cons of microservices")
```

---

## Phase 6: LangGraph for Complex Agents

### 6.1 Stateful Graph Agent
```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
import operator

class AgentState(TypedDict):
    messages: Annotated[list, operator.add]
    next_step: str

def researcher_node(state: AgentState) -> AgentState:
    # Research logic
    return {"messages": [{"role": "researcher", "content": "..."}]}

def writer_node(state: AgentState) -> AgentState:
    # Writing logic  
    return {"messages": [{"role": "writer", "content": "..."}]}

def router(state: AgentState) -> str:
    # Decide next step
    if "needs_research" in state["messages"][-1]["content"]:
        return "researcher"
    return "writer"

# Build graph
workflow = StateGraph(AgentState)
workflow.add_node("researcher", researcher_node)
workflow.add_node("writer", writer_node)
workflow.add_conditional_edges("researcher", router)
workflow.add_edge("writer", END)
workflow.set_entry_point("researcher")

app = workflow.compile()
result = app.invoke({"messages": [{"role": "user", "content": "Write about AI"}]})
```

---

## Quick Patterns Reference

### Error Handling
```python
def safe_tool_call(tool_func, input_data, max_retries=3):
    for attempt in range(max_retries):
        try:
            return tool_func(input_data)
        except Exception as e:
            if attempt == max_retries - 1:
                return f"Error: {e}"
            continue
```

### Streaming Responses
```python
stream = client.chat.completions.create(
    model="gpt-4",
    messages=messages,
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

### Rate Limiting
```python
import time
from functools import wraps

def rate_limit(calls_per_minute: int):
    min_interval = 60.0 / calls_per_minute
    last_call = [0.0]
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_call[0]
            if elapsed < min_interval:
                time.sleep(min_interval - elapsed)
            last_call[0] = time.time()
            return func(*args, **kwargs)
        return wrapper
    return decorator
```
