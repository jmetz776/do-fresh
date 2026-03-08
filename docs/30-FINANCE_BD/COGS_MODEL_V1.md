# DO COGS Model v1 (Finance + Ops)

Date: 2026-03-07
Owner: CFO/BD Working Draft

## Why this exists
We need cost visibility per generated/published output so pricing, margin, and partner negotiations are grounded in data.

## First principle
Track both:
1) **Cost per generated asset**
2) **Cost per delivered/published asset** (includes retries/failures/storage/egress)

---

## Do we need storage/server for video at scale?
**Yes. Absolutely.**
With heavy avatar/faceless generation, persistent object storage + CDN + background processing are mandatory.

Minimum architecture requirement:
- Object storage (S3/R2/GCS/Azure Blob)
- CDN for playback delivery
- Async job workers + queue
- Lifecycle policies (cold/archive/delete)
- Cost alerts + quotas per workspace

Without this, margin gets destroyed by egress and unbounded retention.

---

## Cost buckets to track per output
1. LLM generation (prompt + retries)
2. Voice synthesis (chars/minutes)
3. Video rendering (provider billable time)
4. Image generation (if used)
5. Storage (GB-month)
6. Delivery egress/CDN (GB)
7. Worker compute/queue overhead
8. Failure/retry overhead
9. Human QA/review labor equivalent (optional but recommended)

---

## Required formulas
- `COGS_generated = model + voice + video + image + compute`
- `COGS_delivered = COGS_generated + storage + egress + retry_overhead`
- `GrossMargin% = (Revenue_per_asset - COGS_delivered) / Revenue_per_asset`

Retry overhead model:
- `retry_overhead = base_cost * failure_rate * avg_retry_attempts`

Storage + egress model:
- `storage_cost = avg_file_gb * retention_months * storage_rate`
- `egress_cost = avg_views * avg_stream_gb * egress_rate`

---

## Initial assumptions to validate
- Avatar video: highest COGS due to voice + render + file size
- Faceless: medium COGS
- Image/text: lowest COGS
- Repurpose pack: low generation cost, high value density

---

## Financial control policies (recommended)
1. Default retention windows by tier (e.g., 30/90/365 days)
2. Workspace cost caps + alerting
3. Auto-transcode/lower bitrate defaults for delivery cost control
4. “Regenerate” hard limits per draft to prevent runaway spend
5. Per-workspace profitability reporting

---

## Decision outputs this model should answer weekly
- Which content modes have best contribution margin?
- Which customers/workspaces are margin-negative and why?
- Where can partner discounts improve unit economics most?
- What pricing changes are justified by actual COGS trends?
