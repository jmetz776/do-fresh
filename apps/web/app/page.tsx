"use client";

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';

const INTRO_MS = 3200;

export default function IndexPage() {
  const [canEnter, setCanEnter] = useState(false);
  const [introDone, setIntroDone] = useState(false);
  const [loadingStep, setLoadingStep] = useState(0);

  useEffect(() => {
    const seen = typeof window !== 'undefined' && window.localStorage.getItem('do_intro_seen') === '1';
    if (seen) {
      setIntroDone(true);
      setCanEnter(true);
      setLoadingStep(3);
      return;
    }

    const checkpointA = window.setTimeout(() => setLoadingStep(1), 700);
    const checkpointB = window.setTimeout(() => setLoadingStep(2), 1700);
    const timer = window.setTimeout(() => {
      setCanEnter(true);
      setIntroDone(true);
      setLoadingStep(3);
      window.localStorage.setItem('do_intro_seen', '1');
    }, INTRO_MS);

    return () => {
      window.clearTimeout(checkpointA);
      window.clearTimeout(checkpointB);
      window.clearTimeout(timer);
    };
  }, []);

  const subtitle = useMemo(() => {
    if (canEnter) return 'Ready. Press power to enter workflow';
    if (loadingStep === 2) return 'Scoring demand signals…';
    if (loadingStep === 1) return 'Loading workspace intelligence…';
    return 'Initializing premium workspace…';
  }, [canEnter, loadingStep]);

  return (
    <main className="intro-root">
      <style>{`
        :root {
          --bg: #06070b;
          --bg2: #0a0f1f;
          --line: rgba(99,102,241,.22);
          --text: #eef4ff;
          --muted: #9cb0d7;
          --cyan: #67e8f9;
        }
        .intro-root {
          min-height: 100vh;
          display: grid;
          place-items: center;
          color: var(--text);
          background:
            radial-gradient(1200px 700px at -10% -20%, rgba(103,232,249,.18), transparent 62%),
            radial-gradient(900px 500px at 120% -10%, rgba(99,102,241,.18), transparent 60%),
            linear-gradient(180deg, var(--bg2), var(--bg));
          font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial;
          overflow: hidden;
          position: relative;
        }
        .grid {
          position: absolute;
          inset: 0;
          background-image: linear-gradient(rgba(148,163,184,.07) 1px, transparent 1px), linear-gradient(90deg, rgba(148,163,184,.07) 1px, transparent 1px);
          background-size: 30px 30px;
          mask-image: radial-gradient(circle at 50% 35%, black 28%, transparent 78%);
          pointer-events: none;
          animation: gridBreathe 4.8s ease-in-out infinite;
        }
        .scanline {
          position: absolute;
          left: 0;
          right: 0;
          height: 2px;
          top: -10%;
          background: linear-gradient(90deg, transparent, rgba(103,232,249,.9), transparent);
          box-shadow: 0 0 24px rgba(103,232,249,.45);
          pointer-events: none;
          animation: scan 3.2s ease-in-out infinite;
          opacity: .75;
        }
        .vignette {
          position: absolute;
          inset: 0;
          pointer-events: none;
          background: radial-gradient(circle at 50% 40%, transparent 35%, rgba(2,6,23,.55) 82%);
        }
        .skip {
          position: absolute;
          top: 20px;
          right: 20px;
          border: 1px solid rgba(148,163,184,.35);
          color: #dbe7ff;
          background: rgba(15,23,42,.42);
          border-radius: 999px;
          padding: 8px 12px;
          text-decoration: none;
          font-size: 12px;
        }
        .center {
          text-align: center;
          z-index: 2;
          display: grid;
          justify-items: center;
          align-content: center;
          transform: translateY(-5vh);
        }
        .wordmark {
          letter-spacing: .35em;
          font-size: clamp(1rem, 2.2vw, 1.2rem);
          color: #d9e7ff;
          margin-bottom: 14px;
          opacity: 0;
          animation: fadeInUp .8s ease forwards;
          animation-delay: .25s;
        }
        .do-mark {
          font-size: clamp(4rem, 14vw, 9rem);
          font-weight: 800;
          letter-spacing: -.04em;
          margin: 0;
          display: inline-flex;
          align-items: baseline;
          gap: .015em;
          line-height: 1;
          text-shadow: 0 0 30px rgba(103,232,249,.25);
          opacity: 0;
          animation: fadeInUp .9s ease forwards;
          animation-delay: .7s;
        }
        .o-power {
          display: inline-grid;
          place-items: center;
          width: .68em;
          height: .68em;
          line-height: 1;
          color: var(--cyan);
          text-shadow: 0 0 11px rgba(103,232,249,.34);
          animation: pulse 2s ease-in-out infinite;
          transform: translateY(-.07em);
          margin-left: .012em;
          margin-right: .012em;
          font-size: .82em;
        }
        .sub {
          margin: 10px 0 18px;
          color: var(--muted);
          font-size: 13px;
          letter-spacing: .06em;
          text-transform: uppercase;
          opacity: 0;
          animation: fadeInUp .7s ease forwards;
          animation-delay: 1.25s;
        }
        .trust-line {
          margin-bottom: 18px;
          color: #e6f3ff;
          font-size: clamp(14px, 2.2vw, 18px);
          letter-spacing: .04em;
          text-transform: uppercase;
          font-weight: 900;
          line-height: 1.35;
          padding: 10px 14px;
          border: 1px solid rgba(103,232,249,.45);
          border-radius: 999px;
          background: linear-gradient(180deg, rgba(14,165,233,.2), rgba(15,23,42,.42));
          box-shadow: inset 0 1px 0 rgba(255,255,255,.12), 0 12px 26px rgba(14,165,233,.25);
        }
        .trust-line .accent {
          color: #a5f3fc;
          text-shadow: 0 0 18px rgba(103,232,249,.38);
        }
        .power-link {
          text-decoration: none;
          color: inherit;
          display: inline-block;
          transition: transform .2s ease, opacity .2s ease;
          opacity: ${canEnter ? 1 : 0.35};
          pointer-events: ${canEnter ? 'auto' : 'none'};
          filter: drop-shadow(0 0 18px rgba(103,232,249,.25));
        }
        .power-link:hover { transform: scale(1.03); }
        .intro-actions { display: flex; gap: 10px; flex-wrap: wrap; justify-content: center; }
        .intro-chip {
          border: 1px solid rgba(148,163,184,.35);
          border-radius: 999px;
          padding: 8px 12px;
          font-size: 12px;
          color: #dbe7ff;
          text-decoration: none;
          background: rgba(15,23,42,.45);
        }
        @keyframes pulse {
          0%,100% { text-shadow: 0 0 10px rgba(103,232,249,.28); }
          50% { text-shadow: 0 0 26px rgba(103,232,249,.48); }
        }
        @keyframes fadeInUp {
          from { opacity: 0; transform: translateY(8px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes scan {
          0% { transform: translateY(0); opacity: 0; }
          20% { opacity: .9; }
          100% { transform: translateY(120vh); opacity: 0; }
        }
        @keyframes gridBreathe {
          0%,100% { opacity: .55; }
          50% { opacity: .85; }
        }
        @media (max-width: 760px) {
          .center { transform: translateY(-2vh); }
        }
      `}</style>

      <div className="grid" />
      <div className="scanline" />
      <div className="vignette" />
      <Link className="skip" href="/onboarding" onClick={() => typeof window !== 'undefined' && window.localStorage.setItem('do_intro_seen', '1')}>
        Skip
      </Link>

      <section className="center">
        <div className="wordmark">DEMAND ORCHESTRATOR</div>
        <Link
          href="/onboarding"
          className="power-link"
          onClick={() => {
            if (typeof window !== 'undefined') window.localStorage.setItem('do_intro_seen', '1');
          }}
          aria-label="Enter workflow"
        >
          <h1 className="do-mark">
            D<span className="o-power" aria-hidden="true">⏻</span>
          </h1>
        </Link>
        <p className="sub">{subtitle}</p>
        <div className="trust-line"><span className="accent">Meet your AI-assisted content engine</span> · Trend → Script → Approval → Publish</div>
        <div className="intro-actions">
          <Link className="intro-chip" href="/onboarding" onClick={() => typeof window !== 'undefined' && window.localStorage.setItem('do_intro_seen', '1')}>Enter onboarding</Link>
          <Link className="intro-chip" href="/waitlist">View early access</Link>
        </div>
      </section>
    </main>
  );
}
