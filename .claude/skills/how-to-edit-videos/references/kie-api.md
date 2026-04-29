# kie.ai gpt-image-2 — integration reference

Used by `scripts/generate_images.py`. Source: <https://docs.kie.ai/market/gpt/gpt-image-2-text-to-image>.

## Endpoint

```
POST https://api.kie.ai/api/v1/jobs/createTask
GET  https://api.kie.ai/api/v1/jobs/recordInfo?taskId={id}
```

## Auth

`Authorization: Bearer $KIE_API_KEY` — get the key from <https://kie.ai/api-key>. Stored project-local in `.env`.

## Request body (createTask)

```json
{
  "model": "gpt-image-2-text-to-image",
  "input": {
    "prompt": "<text>",
    "aspect_ratio": "9:16",
    "resolution": "1K"
  }
}
```

- `aspect_ratio` ∈ `auto | 1:1 | 9:16 | 16:9 | 4:3 | 3:4` — we always pass the value derived from `ffprobe` on `source.mp4`. Never hard-coded.
- `resolution` ∈ `1K | 2K | 4K` — we always pass `1K` (Marlon's standing rule, lowest cost). 1:1 cannot be 4K.
- `prompt` — up to 20,000 chars. Keep it tight; longer prompts don't equal better text rendering.

## Response

`createTask` returns `{ code: 200, data: { taskId } }`. Poll `recordInfo` until `data.state == "success"` and pull the PNG URL from `data.resultJson.result_urls[0]` (field paths vary across kie.ai endpoints — the script tries multiple).

## Errors to handle

| code | meaning | action |
|---|---|---|
| 401 | bad key | check `.env` |
| 402 | out of credits | top up at kie.ai before retry |
| 422 | validation (bad aspect ratio / prompt too long) | fix plan row |
| 429 | rate limited | back off, retry |
| 455 | maintenance | wait |
| 550 | queue full | back off |

## Cost note

gpt-image-2 at 1K is the cheapest tier. Expect a few cents per image; a typical 90s ad with 3 images costs <$0.20 in API. **Generation is irreversible spend** — never call before Marlon approves the plan in chat.

## What we do NOT use

- `callBackUrl` — local script polls instead
- `2K` / `4K` resolutions — 1080×1920 video doesn't need them, and 1K decodes faster in the studio preview
- Image-to-image / mask flows — text-to-image only; if Marlon wants to revise an image, he edits the prompt and we re-run with `--force`
