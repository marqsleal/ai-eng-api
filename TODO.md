# Todo Roadmap

## P1 - Product Features + Safety

### Prompting v1 (Opt-in)
- [ ] Add optional `system_instruction` support to `POST /conversations`.
- [ ] Implement prompt merge order:
  base system prompt -> model-specific prompt -> request custom instruction -> user prompt.
- [ ] Extend `ConversationCreate` with optional fields:
  `system_instruction`, `context`.
- [ ] Keep backward compatibility.
- [ ] Segment RAG workflow inputs into **System Prompt** and **General Instructions**.

#### Prompting v1 Workflow
1. Receive `POST /conversations` with optional `system_instruction` and `context`.
2. Segment RAG workflow inputs into:
   System Prompt: high-priority safety, role, and behavior rules.
   General Instructions: task-level guidance, style, and optional RAG-specific directions.
3. Load system prompt and general instructions from `app/prompts/`.
4. Build final prompt using merge order:
   system prompt -> request custom instruction -> general instructions -> user prompt.
5. If `context` is provided, merge or append it according to policy (documented in service logic).
6. Send final prompt to the LLM provider.
7. Persist conversation with original inputs and generated response (plus metadata once P2 lands).

### Prompt Enrichment + Profiles
- [ ] Add enrichment service before LLM call:
  normalize prompt, add metadata context, optional history stitching.
- [ ] Add prompt profiles in config/DB (`assistant_default`, `strict_json`, `support_agent`).

### Safety + Guardrails
- [ ] Enforce max prompt length and blocked content checks.
- [ ] Add optional output schema mode (structured response constraints).

## P2 - Observability + Audit + Rollout

### Persistence + Traceability
- [ ] Store effective prompt sent to model (`final_prompt` / `prompt_trace`) for audit/debug.
- [ ] Store prompt profile/instruction metadata in conversation record.

### Observability
- [ ] Add OTEL span around Ollama generation.
- [ ] Add structured logs for provider/model/tokens/latency/failure type.
- [ ] Log prompt profile, enrichment stages, token impact.
- [ ] Redact sensitive context fields in logs.

### Testing
- [ ] Unit tests for enrichment merge logic.
- [ ] Endpoint tests for:
  no instruction, custom instruction, profile-based instruction, validation failures.

### Rollout Plan
- [ ] Phase 1: opt-in `system_instruction` only.
- [ ] Phase 2: add prompt profiles.
- [ ] Phase 3: add retrieval/context enrichment.
