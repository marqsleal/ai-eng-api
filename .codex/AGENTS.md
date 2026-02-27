# FastAPI Best Practices for AI Agents

FastAPI + Async SQLAlchemy + LLM Architecture Enforcement Guide

This document defines mandatory architectural, implementation, and governance rules for AI agents (including Codex) contributing to this repository.

These rules are deterministic. Soft language such as “should” or “preferably” is intentionally avoided.

---

# Agent Approval Policy

Codex MUST operate in an approval-first mode:

- Do not implement changes without presenting a *plan*.
- Always generate a *diff or change plan* first.
- Await explicit confirmation before producing code changes.

This mirrors CLI Suggest Mode behavior.

---

# 1. Architectural Principles

## 1.1 Layered Architecture (Mandatory)

The system follows strict layering:

```
Router (API Layer)
    ↓
Service (Business Logic)
    ↓
Repository (Persistence)
    ↓
SQLAlchemy Models (Data Layer)
```

Rules:

* Routers MUST NOT contain business logic.
* Services MUST NOT contain raw SQL.
* Repositories MUST NOT commit transactions.
* Models MUST NOT contain business logic.
* LLM provider SDKs MUST NOT be instantiated outside `LLMClient`.

---

## 2. Project Structure

The structure is domain-oriented and must be preserved.

```
├── app/
│   ├── api/ or routers/
│   ├── services/
│   ├── repositories/
│   ├── models/
│   ├── schemas/
│   ├── prompts/
│   ├── llm/
│   ├── core/
│   ├── database/
│   └── main.py
├── migrations/
├── tests/
```

Rules:

* New features must follow this structure.
* Cross-domain imports must use absolute imports.
* No circular dependencies.

---

# 3. Async Rules

## 3.1 Route Behavior

* `async def` routes MUST use non-blocking I/O only.
* Blocking libraries MUST be wrapped with `run_in_threadpool`.
* CPU-intensive tasks MUST be offloaded (Celery or multiprocessing).
* No `time.sleep()` inside async functions.

## 3.2 Database

* SQLAlchemy MUST use async engine.
* All DB writes MUST explicitly call `commit()` in service layer.
* Repositories MUST NOT call `commit()`.

---

# 4. LLM Integration Rules

## 4.1 Provider Abstraction (Mandatory)

All model calls MUST go through:

```
app.llm.client.LLMClient
```

Forbidden:

* Direct SDK usage (Ollama, OpenAI, etc.)
* Inline HTTP calls to providers

---

## 4.2 Generation Pattern

Every generation MUST:

* Capture latency
* Capture input_tokens
* Capture output_tokens
* Persist model_version_id
* Persist provider name
* Persist prompt version
* Enforce server-side parameter bounds

Default parameters:

* temperature: 0.2
* top_p: 0.6
* max_tokens: bounded by model version

No uncontrolled free-form generation in regulated flows.

---

## 4.3 Prompt Governance

* Prompts MUST live in `app/prompts/`
* Every prompt MUST have a version constant
* Prompt version MUST be stored with each conversation
* Inline prompts in routers or services are forbidden
* Prompts MUST be deterministic and static

---

# 5. Security and Compliance

## 5.1 Forbidden Patterns

* Hardcoded secrets
* Logging API keys
* Dynamic `eval`
* Arbitrary code execution
* Returning raw stack traces in production
* Silent failure of provider errors

## 5.2 Required Controls

* Input validation via Pydantic
* Server-side validation of generation parameters
* Sanitization before LLM invocation
* Role-based access enforcement when applicable

---

# 6. Observability

## 6.1 Logging

* Structured logging only
* Include request_id
* No secret exposure

## 6.2 Telemetry

All external calls MUST be wrapped in OpenTelemetry spans:

* DB calls
* LLM calls
* External HTTP calls

Spans MUST include:

* provider
* model
* latency_ms

No sensitive data in span attributes.

---

# 7. Database Conventions

## 7.1 Naming

* snake_case only
* Singular table names
* `_at` suffix for timestamps
* `_date` suffix for date fields

## 7.2 Index Naming Convention

Explicit naming convention must be used for constraints and indexes.

## 7.3 SQL Usage

Complex joins and aggregations MAY be done in SQL.

Business logic MUST NOT be implemented in SQL.

---

# 8. Migrations (Alembic)

* Existing migrations MUST NOT be modified.
* Every schema change requires a new migration.
* Migration files must be reversible.
* Model imports must be correctly configured in env.py.

---

# 9. Testing Requirements

Every new feature MUST include:

* Async test using AsyncClient
* Success case
* Failure case
* Validation error case (if applicable)
* LLM mock if generation involved

---

# 10. Templates

The following templates are mandatory blueprints.

---

## Template — Router

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.services.example_service import ExampleService
from app.schemas.example import ExampleRequest, ExampleResponse

router = APIRouter(prefix="/examples", tags=["examples"])

@router.post("/", response_model=ExampleResponse)
async def create_example(
    payload: ExampleRequest,
    db: AsyncSession = Depends(get_db),
):
    service = ExampleService(db)

    try:
        return await service.create(payload)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
```

---

## Template — Service

```python
import time
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.example_repository import ExampleRepository

class ExampleService:

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ExampleRepository(db)

    async def create(self, payload):
        start = time.perf_counter()

        entity = await self.repo.create(payload)

        await self.db.commit()
        await self.db.refresh(entity)

        latency_ms = int((time.perf_counter() - start) * 1000)

        return {
            "id": entity.id,
            "latency_ms": latency_ms,
        }
```

---

## Template — Repository

```python
class ExampleRepository:

    def __init__(self, db):
        self.db = db

    async def create(self, payload):
        entity = ExampleModel(**payload.model_dump())
        self.db.add(entity)
        return entity
```

---

## Template — LLM Call

```python
import time
from app.llm.client import LLMClient

async def generate_response(model_version, user_prompt: str):
    llm = LLMClient(provider=model_version.provider)

    start = time.perf_counter()

    response = await llm.generate(
        model=model_version.model_name,
        prompt=user_prompt,
        temperature=0.2,
        top_p=0.9,
        max_tokens=512,
    )

    latency_ms = int((time.perf_counter() - start) * 1000)

    return {
        "response": response.text,
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
        "latency_ms": latency_ms,
    }
```

---

## Template — Prompt Definition

```python
SYSTEM_PROMPT_V1 = """
You are a structured assistant.
Do not fabricate information.
If unsure, respond with uncertainty.
"""

PROMPT_VERSION = "v1"
```

---

## Template — Telemetry Span

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("llm.generate") as span:
    span.set_attribute("llm.provider", provider)
    span.set_attribute("llm.model", model_name)
```

---

# 11. Definition of Done

A feature is complete only if:

* Router implemented
* Service implemented
* Repository implemented
* Schema implemented
* Migration generated (if needed)
* Telemetry added
* Logging added
* Tests added
* Token accounting implemented (if LLM used)
* Prompt version persisted (if LLM used)

---

# 12. Absolute Prohibitions

* Business logic in routers
* Direct provider SDK usage
* Inline prompts
* Hardcoded secrets
* Blocking calls in async context
* Missing token accounting
* Missing latency tracking
* Global mutable state

---

# 13. Project Workflow

This project is educational and iterative.
Formal sprint rituals are not required.

However, every change MUST follow a clear and documented workflow to ensure architectural discipline and revision traceability.

The objective is learning quality, not process overhead.

---

# 13.1 Before Starting Any Change

Every new feature, refactor, or bug fix MUST start with a short written definition.

Minimum required structure:

```text
### What is being built or fixed?
Clear description of the problem or improvement.

### Why?
Learning objective or technical motivation.

### Scope
Which layers are affected?
- Router
- Service
- Repository
- Model
- LLM
- Prompt
- Migration

### Risks
- Architecture impact
- Performance impact
- Token usage impact (if LLM-related)
```

This can be written:

* In the GitHub Issue
* Or in a short markdown file under `/docs/notes/`

Development MUST NOT start without this definition.

---

# 13.2 Creating a Branch

Every change MUST be done in a dedicated branch.

## Branch Naming Convention

```text
feature/short-description
bug/short-description
refactor/short-description
study/short-description
```

Examples:

```text
feature/add-conversation-token-tracking
bug/fix-async-session-commit
study/explore-structured-outputs
```

Rules:

* One logical change per branch.
* Do not mix unrelated improvements.
* Branch from main.

---

# 13.3 During Implementation

While working on the issue:

You MUST ensure:

* AGENTS.md rules are respected
* Layer separation is preserved
* LLM abstraction is not bypassed
* Prompt versioning is maintained
* Token accounting is preserved (if LLM involved)
* Latency tracking is preserved (if LLM involved)
* Tests are added or updated
* Logging remains structured

---

# 13.4 Documenting the Solution

Every branch MUST include documentation explaining what was done.

This documentation can live in:

* The Pull Request description (mandatory)
* And optionally in `/docs/changes/<short-description>.md`

Minimum documentation structure:

```text
### Problem
What was missing or incorrect?

### Root Cause (if bug)
Why did it happen?

### Solution
What was implemented?

### Architectural Impact
Which layers were modified?

### Observability Impact
Were new spans or logs added?

### LLM Impact (if applicable)
- Model version changes?
- Prompt version changes?
- Token usage impact?
- Latency impact?
```

This ensures the repository becomes a structured knowledge base.

---

# 13.5 Creating the Pull Request

## PR Title Format

```text
[type] Short description
```

Examples:

```text
[feature] Add prompt version persistence
[bug] Fix async commit ordering
[study] Compare deterministic vs stochastic generation
```

## PR Must Include

* Link to issue (if used)
* Description using documentation template above
* Testing explanation
* Migration explanation (if applicable)

---

# 13.6 Review Checklist (Self-Review)

Before merging your own PR, validate:

* No business logic in routers
* No direct LLM provider calls
* No inline prompts
* Explicit commit in service layer
* No secrets exposed
* No blocking calls in async context
* Tests pass
* Ruff passes
* Code is readable and minimal

If any item fails, fix before merge.

---

# 13.7 After Merge

After merging to main:

* Delete the branch
* Re-read the PR once as a learning review
* Identify potential refactor opportunities
* Add follow-up issues if needed

---

# 13.8 Learning-Oriented Improvements

This project is a learning system.

Each major feature SHOULD aim to teach at least one of:

* Better async patterns
* Better SQL modeling
* Better LLM governance
* Better observability
* Better error handling
* Better architectural separation

If a change does not improve understanding or architecture quality, reconsider its necessity.

---

# 13.9 Continuous Refinement

AGENTS.md is a living document.

If a mistake happens:

1. Fix the code.
2. Improve AGENTS.md to prevent repetition.
3. Document the lesson learned.

The goal is not rigid process.
The goal is disciplined evolution and architectural maturity.

---

# 14. Architecture Decision Records (ADR)

This project maintains lightweight Architecture Decision Records (ADRs) for decisions that affect:

* System architecture
* LLM integration strategy
* Database modeling
* Observability design
* Security controls
* Provider selection
* Major refactors

The goal is traceability and structured learning, not bureaucracy.

An ADR MUST be created when a decision:

* Changes architectural direction
* Introduces a new external dependency
* Modifies LLM behavior significantly
* Affects token usage strategy
* Impacts compliance or security posture
* Alters data modeling patterns

Minor refactors do not require ADRs.

---

# 14.1 ADR Storage Location

ADRs MUST be stored in:

```text
/docs/adr/
```

Naming convention:

```text
ADR-0001-short-title.md
ADR-0002-llm-provider-abstraction.md
ADR-0003-prompt-versioning-strategy.md
```

Numbering MUST be sequential and never reused.

---

# 14.2 ADR Status Lifecycle

Each ADR MUST include a status:

* Proposed
* Accepted
* Rejected
* Superseded (reference replacement ADR)
* Deprecated

Once Accepted, the decision becomes binding unless replaced.

---

# 14.3 Lightweight ADR Template

Each ADR MUST follow this structure:

```text
# ADR-XXXX: Short Title

## Status
Proposed | Accepted | Rejected | Superseded | Deprecated

## Context
What is the technical problem?
What constraints exist?
Why is a decision needed?

Include:
- Architectural background
- LLM implications (if any)
- Data implications (if any)
- Observability implications (if any)

## Decision
What is being decided?

Be explicit and deterministic.
Avoid vague wording.

## Consequences

### Positive
Benefits of this decision.

### Negative
Trade-offs, limitations, technical debt introduced.

### Operational Impact
- Migration required?
- Token cost impact?
- Latency impact?
- Security implications?

## Alternatives Considered
Briefly describe alternatives and why they were rejected.

## Future Revisit Criteria
Under what conditions should this ADR be reconsidered?
```

---

# 14.4 LLM-Specific ADR Requirements

If the ADR involves LLM behavior, it MUST additionally include:

* Model versioning implications
* Prompt versioning implications
* Token cost estimation impact
* Determinism vs stochastic trade-off
* Hallucination risk considerations
* Observability requirements (metrics/spans)

---

# 14.5 When to Write an ADR in This Project

Examples:

* Switching from Ollama to a multi-provider abstraction
* Introducing RAG
* Changing chunking strategy
* Moving from inline prompt composition to template engine
* Adding caching to LLM responses
* Introducing rate limiting
* Changing DB transaction pattern
* Introducing background job processing

Do not create ADRs for:

* Small refactors
* Naming changes
* Minor performance optimizations

---

# 14.6 ADR and Pull Request Integration

If an ADR is created:

* The PR MUST reference the ADR
* The ADR status MUST be set to Proposed during PR
* The ADR MUST be marked Accepted upon merge
* If rejected, mark it Rejected and explain why

---

# 14.7 Educational Reflection (Optional but Recommended)

Since this is a study project, you MAY add:

```text
## Learning Notes
What architectural insight did this decision reinforce?
What would be done differently in production?
```

This section is optional but encouraged for deeper understanding.

---

This document is binding.
AI agents must follow it without deviation.


