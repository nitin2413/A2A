# A2A Multi-Agent System

A modular **Agent-to-Agent (A2A) multi-agent system** designed to solve complex software engineering tasks through collaboration between specialized AI agents.

The system is built around an **Orchestrator** that manages the overall workflow and coordinates multiple autonomous agents, including a **Researcher, Code Generator, and Code Critic**. Instead of relying on a single LLM to perform an entire task, the system decomposes the problem into smaller tasks and assigns each task to the most appropriate agent.

## 🚀 Project Overview

The goal of this project is to build a reliable and extensible architecture for **agentic software development**, where multiple AI agents can communicate, reason, execute tasks, review each other's work, and recover from failures.

A typical workflow looks like:

```text
                    User Request
                         │
                         ▼
                  ┌─────────────┐
                  │ Orchestrator│
                  └──────┬──────┘
                         │
                         ▼
                  ┌─────────────┐
                  │    Planner  │
                  └──────┬──────┘
                         │
              Global Execution Plan
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
     Researcher      Code Generator   Code Critic
          │              │              │
          └──────────────┼──────────────┘
                         ▼
                  Task Results
                         │
                         ▼
                  Validation / Review
                         │
                 ┌───────┴───────┐
                 │               │
              Success          Failure
                 │               │
                 ▼               ▼
              Complete         Replan
```

## 🧠 Core Agents

### 1. Orchestrator

The Orchestrator acts as the central coordinator of the system.

Its responsibilities include:

- Receiving the user's request
- Managing the global execution plan
- Dispatching tasks to specialized agents
- Managing task dependencies
- Tracking task states
- Handling failures and retries
- Coordinating communication between agents
- Maintaining the overall execution flow

### 2. Planner / Researcher

The planning layer converts a high-level user request into a structured execution plan.

It is responsible for:

- Breaking complex problems into smaller tasks
- Identifying task dependencies
- Determining which agent should execute each task
- Providing required resources and context
- Re-planning when tasks fail
- Maintaining a dependency-aware execution graph

The Planner is designed around three core interfaces:

```python
await planner.create_plan(user_request)

await planner.replan(
    user_request=user_request,
    previous_plan=plan,
    failure_context=failure_context
)

await planner.execute(task)
```

### 3. Code Generator

The Code Generator is responsible for implementing software-related tasks.

It can:

- Generate new files
- Modify existing files
- Produce structured file patches
- Work with repository context
- Implement individual tasks from the global plan
- Return structured outputs for downstream validation

The system is designed to distinguish between **creating complete files** and **modifying existing files through patches**, allowing changes to be validated before they are applied.

### 4. Code Critic

The Code Critic reviews the work produced by the Code Generator.

It can evaluate:

- Correctness
- Code quality
- Architecture
- Potential bugs
- Missing requirements
- Implementation issues
- Whether the generated changes satisfy the assigned task

If the implementation fails validation, the system can provide failure context to the planning layer and trigger a re-planning cycle.

---

# ⚙️ Architecture

The project follows a modular architecture where each major responsibility is isolated into its own service.

```text
A2A System
│
├── orchestrator/
│   ├── graph/
│   ├── dispatcher/
│   └── execution/
│
├── services/
│   ├── planner/
│   ├── codegen/
│   ├── critic/
│   └── researcher/
│
├── shared/
│   ├── schemas/
│   ├── configuration/
│   └── utilities/
│
└── tests/
```

This separation makes the system easier to extend with additional agents and execution strategies.

---

# 🔄 Task Management

Tasks are represented using structured schemas containing information such as:

- Task ID
- Parent task ID
- Description
- Assigned agent
- Status
- Dependencies
- Resources
- Input payload
- Output payload
- Attempt count
- Maximum attempts
- Creation/update timestamps
- Error information

Tasks can move through states such as:

```text
PENDING
   │
   ▼
IN_PROGRESS
   │
   ├──────────────► DONE
   │
   ▼
NEEDS_RETRY
   │
   ▼
IN_PROGRESS
   │
   └──────────────► FAILED
```

This allows the Orchestrator to reason about the current state of the entire execution graph.

---

# 🕸️ Dependency-Aware Execution

The system uses a task graph to represent dependencies between tasks.

For example:

```text
Research
   │
   ▼
Architecture
   │
   ├──────────────┐
   ▼              ▼
Backend        Frontend
   │              │
   └──────┬───────┘
          ▼
       Testing
          │
          ▼
        Review
```

Tasks are executed only when their dependencies are satisfied.

This enables parallel execution of independent tasks while preserving the required ordering between dependent tasks.

---

# 🔁 Failure Handling & Replanning

A major objective of the project is to make the multi-agent system more robust than a simple sequential agent pipeline.

When an agent fails, the system can:

1. Detect the failure
2. Record the failure context
3. Update the task state
4. Determine whether the task can be retried
5. Send the failure information back to the Planner
6. Generate an updated plan
7. Continue execution using the revised plan

Conceptually:

```text
Task Failure
     │
     ▼
Failure Context
     │
     ▼
Planner
     │
     ▼
Re-plan
     │
     ▼
Updated Task Graph
     │
     ▼
Orchestrator
     │
     ▼
Continue Execution
```

---

# ⚡ Asynchronous Execution

The system is designed around Python's asynchronous programming model using:

```python
async
await
```

This allows independent tasks and agent operations to be executed concurrently where appropriate.

The goal is to avoid unnecessarily blocking the entire system when one agent is waiting for an LLM response or another external operation.

---

# 💰 Token & Cost Awareness

Since multi-agent systems can generate significantly more LLM calls than a single-agent application, the architecture also considers **token consumption and execution cost**.

The system is designed to support:

- Per-agent model configuration
- Maximum token limits
- Temperature configuration
- Controlled retries
- Task-level execution limits
- Different models for different agents
- Avoiding unnecessary LLM calls

This makes cost management an important part of the architecture rather than an afterthought.

---

# 🧩 LLM Configuration

LLM configuration is separated from the agent implementation.

Example configuration:

```yaml
provider: openrouter
model: <model-name>
temperature: 0.2
max_tokens: 4096
```

This allows individual agents to use different models depending on their requirements.

For example:

```text
Researcher      → reasoning-focused model
Planner         → reasoning/planning model
Code Generator  → coding model
Code Critic     → reasoning/code-review model
```

The architecture is intended to remain provider-agnostic.

---

# 🛠️ Technology Stack

### Core

- Python
- AsyncIO
- Pydantic
- YAML configuration
- uv

### AI / LLM

- LLM APIs
- LiteLLM
- LangChain integrations
- OpenRouter
- Local / remote model support

### Agent Architecture

- A2A concepts
- Multi-agent orchestration
- Tool calling
- Structured outputs
- Agent-to-agent communication
- Task graphs
- Planning and replanning

### Development

- Git
- GitHub
- pytest
- Docker
- Virtual environments
- `uv`

---

# 🎯 Design Goals

The project is being developed around several key principles:

### Modularity

Each agent should have a clearly defined responsibility and interface.

### Reliability

Agent failures should not necessarily terminate the entire workflow.

### Extensibility

New agents should be easy to add without rewriting the entire system.

### Observability

The system should maintain enough task and execution state to understand what happened during a run.

### Cost Awareness

LLM calls and token usage should be controlled because multi-agent systems can quickly become expensive.

### Asynchronous Execution

Independent operations should be able to execute concurrently.

### Structured Communication

Agents should exchange structured data rather than relying entirely on unstructured text.

---

# 🔮 Future Improvements

Planned improvements include:

- [ ] Complete A2A protocol integration
- [ ] Improved inter-agent communication
- [ ] Persistent agent memory
- [ ] Tool-use framework
- [ ] Better context management
- [ ] Token/cost tracking dashboard
- [ ] Agent evaluation framework
- [ ] Automated code testing
- [ ] Sandboxed code execution
- [ ] Improved failure recovery
- [ ] Persistent task state
- [ ] Multi-model routing
- [ ] Human-in-the-loop approval
- [ ] Distributed agent execution
- [ ] Production deployment

---

# 📌 Project Status

This project is currently under active development.

The architecture and interfaces are evolving as new components are implemented and tested. The primary focus is building a reliable foundation for **multi-agent orchestration, asynchronous execution, planning, code generation, code review, and failure recovery**.

---

## 🎓 Motivation

This project is being developed to explore how multiple specialized AI agents can collaborate on complex software engineering problems.

Rather than treating an LLM as a single general-purpose assistant, the project experiments with a **team-of-agents architecture**, where each agent has a specialized responsibility and the Orchestrator coordinates their work.

The long-term goal is to create a system capable of taking a high-level software requirement and autonomously progressing through:

```text
Requirement
     ↓
Planning
     ↓
Research
     ↓
Implementation
     ↓
Code Review
     ↓
Testing
     ↓
Failure Recovery
     ↓
Replanning
     ↓
Final Result
```
