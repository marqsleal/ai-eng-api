# Todo Roadmap

## P0 - Critical Foundation

### Runtime + Startup Reliability
- [ ] Verify Ollama reachability on app startup.
- [ ] Optionally verify `OLLAMA_DEFAULT_MODEL` exists; log actionable warning/error.

### API Contract Consistency
- [ ] Define standard error schema: `code`, `message`, `details`.
- [ ] Add global exception handlers to enforce consistent error payloads.
- [ ] Add typed query schemas for list routes: `limit`, `offset`, `order_by`.
- [ ] Preserve backward compatibility for existing clients.

### Architecture Boundaries
- [ ] Move endpoint orchestration into service layer.
- [ ] Keep endpoint functions as pure HTTP adapters.

### Baseline Documentation + Images
- [ ] Document in README/Make docs that `docker compose up` bootstraps models via `ollama-init`.
- [ ] Clarify `llm_up` vs full stack startup behavior.
- [ ] Pin container image tags (replace `latest` for Ollama/Jaeger with explicit versions).
- [ ] Document image upgrade policy.

## P1 - Product Features + Safety

### Prompting v1 (Opt-in)
- [ ] Add optional `system_instruction` support to `POST /conversations`.
- [ ] Implement prompt merge order:
  base system prompt -> model-specific prompt -> request custom instruction -> user prompt.
- [ ] Extend `ConversationCreate` with optional fields:
  `system_instruction`, `profile_id`, `context`.
- [ ] Keep backward compatibility.

### Prompt Enrichment + Profiles
- [ ] Add enrichment service before LLM call:
  normalize prompt, add metadata context, optional history stitching.
- [ ] Add prompt profiles in config/DB (`assistant_default`, `strict_json`, `support_agent`).

### Safety + Guardrails
- [ ] Enforce max prompt length and blocked content checks.
- [ ] Add optional output schema mode (structured response constraints).

### API Documentation (Swagger)
- [ ] Add Swagger/OpenAPI module integration.
- [ ] Expose interactive docs endpoint (e.g. `/docs`) and raw OpenAPI JSON endpoint.
- [ ] Ensure schemas/examples stay aligned with request/response models.

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
