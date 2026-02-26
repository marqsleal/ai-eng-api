# API Routes (curl examples)

Assumes base URL `http://localhost:8000`. Replace IDs with real values.

## Health

### GET /health/db

```bash
curl -s http://localhost:8000/health/db
```

Expected output:

```json
{"status":"ok"}
```

## Users

### POST /users

```bash
curl -s -X POST http://localhost:8000/users \
  -H 'Content-Type: application/json' \
  -d '{"email":"ana@example.com"}'
```

Expected output (201):

```json
{"id":"<uuid>","email":"ana@example.com","created_at":"<iso-datetime>","is_active":true}
```

### GET /users

```bash
curl -s http://localhost:8000/users
```

Expected output (200):

```json
[{"id":"<uuid>","email":"ana@example.com","created_at":"<iso-datetime>","is_active":true}]
```

### GET /users/{user_id}

```bash
curl -s http://localhost:8000/users/<user_id>
```

Expected output (200):

```json
{"id":"<uuid>","email":"ana@example.com","created_at":"<iso-datetime>","is_active":true}
```

### PATCH /users/{user_id}

```bash
curl -s -X PATCH http://localhost:8000/users/<user_id> \
  -H 'Content-Type: application/json' \
  -d '{"email":"bea@example.com"}'
```

Expected output (200):

```json
{"id":"<uuid>","email":"bea@example.com","created_at":"<iso-datetime>","is_active":true}
```

### DELETE /users/{user_id}

```bash
curl -s -X DELETE http://localhost:8000/users/<user_id> -i
```

Expected output:

- `204 No Content`

## Model Versions

### POST /model-versions

```bash
curl -s -X POST http://localhost:8000/model-versions \
  -H 'Content-Type: application/json' \
  -d '{"provider":"openai","model_name":"gpt-4.1","version_tag":"2026-02-25"}'
```

Expected output (201):

```json
{"id":"<uuid>","provider":"openai","model_name":"gpt-4.1","version_tag":"2026-02-25","created_at":"<iso-datetime>","is_active":true}
```

### GET /model-versions

```bash
curl -s http://localhost:8000/model-versions
```

Expected output (200):

```json
[{"id":"<uuid>","provider":"openai","model_name":"gpt-4.1","version_tag":"2026-02-25","created_at":"<iso-datetime>","is_active":true}]
```

### GET /model-versions/{model_version_id}

```bash
curl -s http://localhost:8000/model-versions/<model_version_id>
```

Expected output (200):

```json
{"id":"<uuid>","provider":"openai","model_name":"gpt-4.1","version_tag":"2026-02-25","created_at":"<iso-datetime>","is_active":true}
```

### PATCH /model-versions/{model_version_id}

```bash
curl -s -X PATCH http://localhost:8000/model-versions/<model_version_id> \
  -H 'Content-Type: application/json' \
  -d '{"version_tag":"2026-02-26"}'
```

Expected output (200):

```json
{"id":"<uuid>","provider":"openai","model_name":"gpt-4.1","version_tag":"2026-02-26","created_at":"<iso-datetime>","is_active":true}
```

### DELETE /model-versions/{model_version_id}

```bash
curl -s -X DELETE http://localhost:8000/model-versions/<model_version_id> -i
```

Expected output:

- `204 No Content`

## Conversations

### POST /conversations

```bash
curl -s -X POST http://localhost:8000/conversations \
  -H 'Content-Type: application/json' \
  -d '{"user_id":"<user_id>","model_version_id":"<model_version_id>","prompt":"hello","response":"world","temperature":0.2}'
```

Expected output (201):

```json
{
  "id":"<uuid>",
  "user_id":"<uuid>",
  "model_version_id":"<uuid>",
  "prompt":"hello",
  "response":"world",
  "temperature":0.2,
  "top_p":null,
  "max_tokens":null,
  "input_tokens":null,
  "output_tokens":null,
  "total_tokens":null,
  "latency_ms":null,
  "created_at":"<iso-datetime>",
  "is_active":true
}
```

### GET /conversations

```bash
curl -s http://localhost:8000/conversations
```

Expected output (200):

```json
[{"id":"<uuid>","user_id":"<uuid>","model_version_id":"<uuid>","prompt":"hello","response":"world","created_at":"<iso-datetime>","is_active":true}]
```

### GET /conversations?user_id=...

```bash
curl -s "http://localhost:8000/conversations?user_id=<user_id>"
```

Expected output (200):

```json
[{"id":"<uuid>","user_id":"<uuid>","model_version_id":"<uuid>","prompt":"hello","response":"world","created_at":"<iso-datetime>","is_active":true}]
```

### GET /conversations/{conversation_id}

```bash
curl -s http://localhost:8000/conversations/<conversation_id>
```

Expected output (200):

```json
{"id":"<uuid>","user_id":"<uuid>","model_version_id":"<uuid>","prompt":"hello","response":"world","created_at":"<iso-datetime>","is_active":true}
```

### PATCH /conversations/{conversation_id}

```bash
curl -s -X PATCH http://localhost:8000/conversations/<conversation_id> \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"new prompt","temperature":0.3}'
```

Expected output (200):

```json
{"id":"<uuid>","user_id":"<uuid>","model_version_id":"<uuid>","prompt":"new prompt","response":"world","temperature":0.3,"created_at":"<iso-datetime>","is_active":true}
```

### DELETE /conversations/{conversation_id}

```bash
curl -s -X DELETE http://localhost:8000/conversations/<conversation_id> -i
```

Expected output:

- `204 No Content`

## Negative Example

### POST /conversations (missing user)

```bash
curl -s -X POST http://localhost:8000/conversations \
  -H 'Content-Type: application/json' \
  -d '{"user_id":"11111111-1111-1111-1111-111111111111","model_version_id":"<model_version_id>","prompt":"x","response":"y"}'
```

Expected output (404):

```json
{"detail":"User not found"}
```
