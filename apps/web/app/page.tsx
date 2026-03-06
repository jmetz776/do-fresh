"use client";

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';

const INTRO_MS = 10000;

export default function IndexPage() {
  const [canEnter, setCanEnter] = useState(false);
  const [introDone, setIntroDone] = useState(false);

  useEffect(() => {
    const seen = typeof window !== 'undefined' && window.localStorage.getItem('do_intro_seen') === '1';
    if (seen) {
      setIntroDone(true);
      setCanEnter(true);
      return;
    }

    const timer = window.setTimeout(() => {
      setCanEnter(true);
      setIntroDone(true);
      window.localStorage.setItem('do_intro_seen', '1');
    }, INTRO_MS);

    return () => window.clearTimeout(timer);
  }, []);

  const subtitle = useMemo(() => (canEnter ? 'Press power to enter workflow' : 'Initializing…'), [canEnter]);

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
        .center { text-align: center; z-index: 2; }
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
          margin: 10px 0 24px;
          color: var(--muted);
          font-size: 14px;
          letter-spacing: .06em;
          text-transform: uppercase;
          opacity: 0;
          animation: fadeInUp .7s ease forwards;
          animation-delay: 1.25s;
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
      </section>
    </main>
  );
}
