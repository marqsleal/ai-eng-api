# API Quick Routes

Base URL: `http://localhost:8000`

## API Docs

- Swagger UI: `http://localhost:8000/docs`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

Use the JSON payloads below in Swagger UI (`Try it out`).

## 1) Health Check

- Method/Path: `GET /health/db`
- Request body: none
- Expected response:

```json
{"status":"ok"}
```

## 2) Bootstrap Data

### Create User

- Method/Path: `POST /users`
- Request body:

```json
{
  "email": "test-user@example.com"
}
```

### Create Model Version

- Method/Path: `POST /model-versions`
- Request body:

```json
{
  "provider": "ollama",
  "model_name": "llama3.2:3b",
  "version_tag": "v1"
}
```

## 3) Create Conversation (LLM Auto-generation)

Requirements:
- `model_version.provider` must be `ollama`
- API must reach Ollama

- Method/Path: `POST /conversations`
- Request body:

```json
{
  "user_id": "<USER_ID>",
  "model_version_id": "<MODEL_VERSION_ID>",
  "prompt": "Reply exactly: LOCAL_OK",
  "system_instruction": "You are a helpful assistant.",
  "context": "Use the retrieved facts only.",
  "temperature": 0,
  "max_tokens": 16
}
```

- Expected response:

```json
{
  "id": "<CONVERSATION_ID>",
  "user_id": "<USER_ID>",
  "model_version_id": "<MODEL_VERSION_ID>",
  "prompt": "Reply exactly: LOCAL_OK",
  "response": "<generated>",
  "created_at": "<iso-datetime>",
  "is_active": true
}
```

## 4) Common Reads

- `GET /users`
- `GET /model-versions`
- `GET /conversations`
- `GET /conversations?user_id=<USER_ID>`

## 5) Update + Delete Examples

### Update User

- Method/Path: `PATCH /users/{user_id}`
- Request body:

```json
{
  "email": "updated-user@example.com"
}
```

### Delete User

- Method/Path: `DELETE /users/{user_id}`
- Request body: none

## 6) Negative Case

- Method/Path: `POST /conversations`
- Request body:

```json
{
  "user_id": "11111111-1111-1111-1111-111111111111",
  "model_version_id": "<MODEL_VERSION_ID>",
  "prompt": "x"
}
```

Expected response:

```json
{"detail":"User not found"}
```
