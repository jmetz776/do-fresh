# Demand Orchestrator Intelligence Whitepaper (Living Draft)

Version: 0.1 (living)
Updated: 2026-03-06

## Abstract
Demand Orchestrator converts raw trend data into explainable, brand-aligned, and outcome-aware content decisions. The system combines ingestion, scoring, learning feedback, and campaign graph generation to create practical queue outputs for publishing operations.

## Problem
Most trend tools stop at discovery. Teams still face a gap from “interesting signal” to “high-confidence content actions” tied to measurable outcomes.

## System Overview
1. Signal Ingestion (Apify + source pipelines)
2. Feature Engineering (velocity, freshness, relevance, saturation, risk)
3. Ranking & Explainability (score + confidence + rationale)
4. Queue Planning (content mix by plan/caps)
5. Outcome Feedback (accept/reject/publish + analytics)
6. Adaptive Learning (workspace profile updates)

## Scoring v2 (Current)
Final quality score is a weighted function of:
- trend velocity
- freshness
- brand relevance
- trend baseline
minus penalties for:
- saturation
- policy risk

Outputs include:
- confidence
- explanation object (`whyNow`, `whyBrand`, `whyChannel`, `riskNote`)

## Learning Loop
Feedback and outcomes update workspace weighting profile over time:
- accepted/rejected signals tune relevance weighting
- published outcomes increase source confidence
- reject patterns increase penalty controls

## Narrative Graph
A signal can generate multiple campaign branches (angles):
- quick take
- contrarian
- checklist
- case-style
- FAQ

This shifts output from one-off drafts to repeatable campaign systems.

## Reliability and Safety
- Provider health checks + degraded mode notices
- Key failover where supported
- Maintenance messaging controls
- Premium feature caps and plan-aware allocation

## Roadmap Notes
This whitepaper is living and should be updated as:
- scoring weights evolve,
- learning policies change,
- attribution model matures,
- marketplace/provider systems are integrated.
