# DO Demo Checklist (5-Minute Operator Flow)

Use this for a clean, repeatable end-to-end demo in `/ops`.

## 0) Safety setup (30 sec)
- Channels must be `x` only (no LinkedIn)
- Confirm API is up: `http://127.0.0.1:8000/health`
- Open UI: `http://127.0.0.1:3000/ops`

## 1) Create source
In **Create Source**:
- Type: `CSV`
- Payload:

```csv
title,body
DO demo test,Quick DemandOrchestrator flow verification.
```

- Click **Create Source**

## 2) Normalize
In **Normalize + Generate**:
- Click **Normalize Source**
- Confirm source items > 0

## 3) Generate
Still in **Normalize + Generate**:
- Channels: `x`
- Variant count: `1`
- Click **Generate**

## 4) Approve one draft
In **Content Queue**:
- Find the new X draft
- Optional: quick caption edit
- Click **Approve**

## 5) Schedule
In the same draft card:
- Set publish time to ~5 minutes ahead
- Timezone: `America/New_York`
- Click **Schedule**

## 6) Publish now
In **Publish Control**:
- Click **Run Publisher Now**

## 7) Success criteria
Pass if all are true:
- Content item shows `x • published`
- Dashboard `published` count increments
- Provider Audit Trail shows a successful publish job

## If it fails
Capture and report exactly:
- Step number
- On-screen error text
- Timestamp
- Draft/content id (if visible)

Format:
`broke at step <n>: <exact error>`
