# 🚨 AI Incident Response Agent

An AI-powered incident response system that helps developers and SRE teams investigate software incidents by combining **live incident telemetry, GitHub repository intelligence, historical incident memory, and LLM-powered reasoning**.

The goal is to move incident response beyond simply monitoring metrics — the agent connects the current incident with the application's codebase and previous incidents to provide **evidence-based diagnosis and actionable recovery recommendations**.

---

# 🚀 What's Improved

The current repository extends the functionality demonstrated in the original project video with a more complete, evidence-driven incident investigation and recovery workflow.

The original demonstration focused on the core concept of AI-assisted incident response. The current implementation expands that workflow by connecting incident telemetry with the **actual application repository, relevant source/configuration files, historical incident experience, controlled recovery, verification, and confirmed incident learning**.

### Key improvements

#### 🔎 Repository-Aware Investigation

The agent does not rely only on monitoring metrics.

It analyzes the connected GitHub repository to understand:

- Application structure
- Frontend and backend components
- Frameworks and technologies
- APIs and external dependencies
- Database indicators
- Deployment configuration
- Relevant source files
- Relevant configuration files
- Repository-level failure mechanisms

The agent can inspect the actual files that are relevant to the incident before forming a diagnosis.

---

#### 🧠 Evidence-Based Diagnosis

Telemetry provides symptoms and runtime signals, but telemetry alone does not prove that a particular component is responsible for an incident.

The investigation therefore combines:

```text
Current Telemetry
       +
Application Context
       +
Repository Evidence
       +
Historical Experience
       ↓
AI Reasoning
       ↓
Evidence-Based Diagnosis




Current Incident
      │
      ▼
┌─────────────────────┐
│ Incident Telemetry  │
│ latency / errors /  │
│ CPU / memory / DB   │
└──────────┬──────────┘
           │
           ▼
┌──────────────────────────┐
│ Repository Intelligence  │
│ GitHub code / structure  │
│ configuration / changes  │
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│ Relevant File Analysis   │
│ source / config / APIs   │
│ deployment mechanisms    │
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│ Historical Memory        │
│ Hindsight incident       │
│ experiences              │
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│ AI Incident Analysis     │
│ OpenRouter LLM           │
│ reasoning + evidence     │
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│ Diagnosis & Recommendation│
│ root cause + next action │
└────────────┬─────────────┘
             │
             ▼
      Human Approval
             │
             ▼
      Recovery Action
             │
             ▼
        Verification
             │
       ┌─────┴─────┐
       │           │
     Success      Failure
       │           │
       ▼           ▼
   RESOLVED   INVESTIGATE AGAIN
       │
       ▼
Confirmed Learning
       │
       ▼
    Hindsight