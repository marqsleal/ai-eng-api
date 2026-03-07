# Todo Roadmap

## P0 - Document Ingestion Workflow (RAG Foundation)

### Data Model + Contracts
- [ ] Add `document_sources` schema (type, uri, tenant, owner, classification, status).
- [ ] Add `documents` schema (source_id, title, checksum, version, effective_date, is_active).
- [ ] Add `document_chunks` schema (document_id, chunk_index, chunk_text, metadata).
- [ ] Define ingestion status contract (`pending`, `processing`, `ready`, `failed`).
- [ ] Add idempotency contract using content checksum/hash.

### Source Registration + Validation
- [ ] Support source registration for v1 (`git`, `s3`, `upload`).
- [ ] Enforce allowlist for source URIs/paths (no arbitrary public URLs).
- [ ] Validate tenant/owner/classification metadata at ingestion request time.

### Extraction + Normalization
- [ ] Implement extraction pipeline for v1 formats (`md`, `pdf` text-based, `html`, `txt`).
- [ ] Normalize extracted content to UTF-8 plain text with stable metadata.
- [ ] Reject low-quality/OCR-poor scanned documents in v1.
- [ ] Persist extraction failures with reason codes for retry/debug.

### Chunking + Embedding + Indexing
- [ ] Implement chunking strategy with overlap and section boundary preservation.
- [ ] Persist chunk-level traceability (`doc_id`, `version`, `section`, `chunk_id`).
- [ ] Generate embeddings with pinned model version and config.
- [ ] Upsert vectors with metadata filters (`tenant`, `classification`, `doc_type`, `version`).
- [ ] Add ingestion-time duplicate detection (checksum + similarity guardrails).

### Publish + Versioning
- [ ] Implement async job workflow (`extract -> chunk -> embed -> index -> publish`).
- [ ] Keep previous document version active until new version reaches `ready`.
- [ ] Add reindex workflow for updated documents with zero-downtime swap.
- [ ] Implement soft-delete for docs plus retention-based vector cleanup.

### Retrieval Readiness + Observability
- [ ] Enforce retrieval-time metadata filters for tenant/classification authorization.
- [ ] Persist ingestion run audit trail (counts, durations, embedding model, failures).
- [ ] Add ingestion metrics/logs (success rate, failure rate, processing latency).
- [ ] Add endpoint/admin visibility for ingestion status and failure diagnostics.

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
