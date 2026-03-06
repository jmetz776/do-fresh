# Background Template Sourcing Runbook (v1)

## Decision
Start with licensed stock + internal curation. No custom generation in v1.

## Source Policy (Required)
Allowed license types:
- commercial
- royalty_free
- owned
- custom_contract

Required provenance fields for ingest:
- source
- licenseType
- licenseRef

## First Pack Target (30 templates)
- Newsroom / Macro: 8
- Explainer / Minimal: 8
- Creator / Promo: 6
- Industry (ecom/real-estate/health): 8

## Asset Prep Requirements
For each template, produce 3 variants:
- vertical_9_16
- square_1_1
- landscape_16_9

Readability threshold:
- readabilityScore >= 0.70

## Workflow
1. Source candidate assets from licensed providers.
2. Normalize to 3 aspect ratios.
3. Score readability + safe zones.
4. Ingest as pending_review via API.
5. Approve templates that pass policy/readability.

## Ingest API
POST /video/background-templates/ingest

## Approve API
POST /video/background-templates/{template_id}/approve

## Example ingest payload
See: `apps/api/app/config/background_template_ingest_sample.json`

## Definition of Done (v1)
- 30 approved templates live
- At least 10 free-tier templates
- All templates have provenance + licenseRef
- All templates pass readability threshold
- Faceless render jobs carry selected backgroundTemplateId
