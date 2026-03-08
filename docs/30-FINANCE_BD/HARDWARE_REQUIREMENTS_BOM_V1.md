# Hardware Requirements + BOM v1 (Video-Heavy DO Operations)

Date: 2026-03-07
Scope: Internal production + validation environment for high-volume avatar/faceless generation workflows.

## Important pricing note
Automated live scraping for B&H and some Dell pages is partially blocked (anti-bot/dynamic rendering).
This BOM includes practical market price ranges and direct vendor quote paths; finalize with live quotes from your Dell account rep and B&H carts.

---

## 1) What is required at minimum?
For heavy video generation and delivery:
- Compute nodes for orchestration, QC, and render-job handling
- Fast storage + backup
- Reliable network and power protection
- Monitoring/observability workstation

Yes: storage/server capacity is necessary at scale.

---

## 2) Suggested deployment profile (starting footprint)

### A) Orchestration/API Node (x1)
- Vendor target: Dell Precision tower or rack equivalent
- Suggested spec:
  - CPU: Intel i9 / Xeon class (16+ cores)
  - RAM: 64 GB (expandable to 128 GB)
  - NVMe: 2 TB
  - GPU: optional for local media QA/transcoding (RTX 4070+)
- Estimated range: **$2,800–$4,800**

### B) Worker/Media Node (x1)
- Purpose: async jobs, media transforms, fallback local rendering/testing
- Suggested spec:
  - CPU: 16+ cores
  - RAM: 64–128 GB
  - NVMe: 4 TB
  - GPU: RTX 4070 Ti / 4080 class (optional but strongly recommended for local media ops)
- Estimated range: **$3,500–$6,500**

### C) Storage NAS (x1)
- Vendor target: Synology/QNAP class 4- to 8-bay
- Suggested spec:
  - 4-bay minimum, RAID-5/RAID-6 capable
  - 32–64 TB raw (expandable)
  - 10GbE optional but recommended
- Estimated NAS chassis + drives range: **$1,800–$4,500**

### D) Backup target (x1)
- External backup/NAS/cloud backup gateway
- Estimated range: **$800–$2,000**

### E) Networking + Power
- 10GbE switch (or high-quality 2.5GbE if budget constrained)
- UPS (line-interactive or online for core nodes)
- Estimated range: **$700–$2,500**

### F) Operator workstation (x1)
- For QA, monitoring, and clip validation
- Suggested spec: 32 GB RAM, strong CPU, color-accurate display
- Estimated range: **$1,800–$3,500**

### G) Color-accurate monitor(s)
- Suggested: 27" 4K IPS (Dell UltraSharp class)
- Estimated per monitor: **$450–$900**

---

## 3) Total budget bands
- **Lean start** (no heavy local GPU dependence): **$11K–$16K**
- **Balanced** (recommended): **$16K–$24K**
- **High-resilience** (extra redundancy/headroom): **$24K–$38K**

---

## 4) Ongoing monthly infrastructure cost categories
- Cloud object storage (video artifacts)
- CDN/egress (playback and downloads)
- Background job compute
- Logs/monitoring
- Backup/archive retention

These recurring costs usually exceed one-time hardware over time if retention and egress are unmanaged.

---

## 5) Procurement starting points (as requested)

### Dell (primary)
- Use Dell account rep for Precision/PowerEdge bundle quote.
- Ask for:
  - business discount tiers
  - warranty uplift
  - volume quote for node + monitor bundle
  - lead-time guarantee

### B&H Photo (secondary)
- Use B&H for NAS, drives, network gear, UPS, and select displays.
- Ask for:
  - bulk/education/business pricing
  - lead-time confirmation for NAS drives

---

## 6) Quote pack checklist (what to request tomorrow)
1. Dell quote: Orchestration node + Worker node + 2 monitors + warranty
2. B&H quote: NAS + drives + switch + UPS + backup drives
3. Side-by-side TCO sheet:
   - upfront hardware
   - monthly cloud/storage/egress
   - replacement cycle assumptions (36 months)

---

## 7) Recommendation
Start with the **Balanced profile** and enforce strict media lifecycle policies:
- default retention windows
- archive/cold storage rules
- egress controls
- workspace-level usage alerts

This will protect margins as content volume scales.
