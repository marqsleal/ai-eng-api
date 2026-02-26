# Todo Roadmap

1. **Docs + Startup Behavior**
- [ ] Document in README/Make docs that `docker compose up` now bootstraps models via `ollama-init`.
- [ ] Clarify `llm_up` vs full stack startup behavior.
- [ ] Pin container image tags (replace `latest` for Ollama/Jaeger with explicit versions).
- [ ] Document image upgrade policy.

2. **LLM Startup Hardening**
- [ ] Verify Ollama reachability on app startup.
- [ ] Optionally verify `OLLAMA_DEFAULT_MODEL` exists; log actionable warning/error.

3. **Error Contract Standardization**
- [ ] Define standard error schema: `code`, `message`, `details`.
- [ ] Add global exception handlers to enforce consistent error payloads.

4. **API Query Schema Improvements**
- [ ] Add typed query schemas for list routes: `limit`, `offset`, `order_by`.
- [ ] Preserve backward compatibility for existing clients.

5. **Service/Repository Boundary Cleanup**
- [ ] Move endpoint orchestration into service layer.
- [ ] Keep endpoint functions as pure HTTP adapters.

6. **Prompting v1 (Opt-in first)**
- [ ] Add optional `system_instruction` support to `POST /conversations`.
- [ ] Implement prompt merge order:
  base system prompt -> model-specific prompt -> request custom instruction -> user prompt.
- [ ] Extend `ConversationCreate` with optional fields:
  `system_instruction`, `profile_id`, `context`.
- [ ] Keep backward compatibility.

7. **Prompt Enrichment + Profiles**
- [ ] Add enrichment service before LLM call:
  normalize prompt, add metadata context, optional history stitching.
- [ ] Add prompt profiles in config/DB (`assistant_default`, `strict_json`, `support_agent`).

8. **Safety + Guardrails**
- [ ] Enforce max prompt length and blocked content checks.
- [ ] Add optional output schema mode (structured response constraints).

9. **Persistence + Traceability**
- [ ] Store effective prompt sent to model (`final_prompt` / `prompt_trace`) for audit/debug.
- [ ] Store prompt profile/instruction metadata in conversation record.

10. **Observability**
- [ ] Add OTEL span around Ollama generation.
- [ ] Add structured logs for provider/model/tokens/latency/failure type.
- [ ] Log prompt profile, enrichment stages, token impact.
- [ ] Redact sensitive context fields in logs.

11. **Testing**
- [ ] Unit tests for enrichment merge logic.
- [ ] Endpoint tests for:
  no instruction, custom instruction, profile-based instruction, validation failures.

12. **Rollout Plan**
- [ ] Phase 1: opt-in `system_instruction` only.
- [ ] Phase 2: add prompt profiles.
- [ ] Phase 3: add retrieval/context enrichment.
