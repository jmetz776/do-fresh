"use client";

import { useEffect, useMemo, useRef, useState } from 'react';

type Props = {
  context: 'onboarding' | 'studio';
  stage?: string;
};

function buildHelpText(context: Props['context'], stage?: string) {
  if (context === 'onboarding') {
    if (stage?.startsWith('story-')) {
      return 'Take your time on this slide. When you are ready, click Next. You can turn voiceover on or off anytime.';
    }
    if (stage === 'setup-1') {
      return 'Start by selecting only the channels you want to connect now. You can skip others and add them later.';
    }
    if (stage === 'setup-2') {
      return 'Fill in your brand context clearly. Better details here improve script quality and originality downstream.';
    }
    if (stage === 'setup-3') {
      return 'Finish avatar setup when ready, then return and click I completed avatar setup.';
    }
    return 'Use Back and Next to move at your own pace. If anything feels unclear, I can walk you through it.';
  }

  return 'Start from the flow card: pick presenter, create avatar video, then review performance before scheduling.';
}

export default function AIAssistHelper({ context, stage }: Props) {
  const [open, setOpen] = useState(false);
  const [nudge, setNudge] = useState(false);
  const [playing, setPlaying] = useState(false);
  const [msg, setMsg] = useState('');
  const idleRef = useRef<number | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const clickRef = useRef<{ key: string; count: number; ts: number }>({ key: '', count: 0, ts: 0 });

  const helpText = useMemo(() => buildHelpText(context, stage), [context, stage]);

  useEffect(() => {
    const reset = () => {
      setNudge(false);
      if (idleRef.current) window.clearTimeout(idleRef.current);
      idleRef.current = window.setTimeout(() => {
        setMsg('Looks like you may be paused. Want a quick walkthrough?');
        setNudge(true);
      }, 30000);
    };

    const onClick = (ev: Event) => {
      reset();
      const target = ev.target as HTMLElement | null;
      if (!target) return;
      const btn = target.closest('button,a,[role="button"]') as HTMLElement | null;
      const key = `${btn?.tagName || target.tagName}:${(btn?.textContent || target.textContent || '').trim().slice(0, 40)}`;
      const now = Date.now();
      const prev = clickRef.current;
      if (prev.key === key && now - prev.ts < 12000) {
        clickRef.current = { key, count: prev.count + 1, ts: now };
      } else {
        clickRef.current = { key, count: 1, ts: now };
      }
      if (clickRef.current.count >= 3) {
        setMsg('I noticed repeated clicks. I can guide you through this step.');
        setNudge(true);
      }
    };

    const onInvalid = () => {
      setMsg('Some required fields still need attention. I can point you to the exact next step.');
      setNudge(true);
    };

    reset();
    const events = ['mousemove', 'keydown', 'scroll', 'touchstart'];
    events.forEach((e) => window.addEventListener(e, reset, { passive: true }));
    window.addEventListener('click', onClick, { passive: true });
    document.addEventListener('invalid', onInvalid, true);

    return () => {
      if (idleRef.current) window.clearTimeout(idleRef.current);
      events.forEach((e) => window.removeEventListener(e, reset));
      window.removeEventListener('click', onClick);
      document.removeEventListener('invalid', onInvalid, true);
      if (audioRef.current) audioRef.current.pause();
      if ('speechSynthesis' in window) window.speechSynthesis.cancel();
    };
  }, []);

  async function speak() {
    setPlaying(true);
    setMsg('Preparing premium voice...');
    try {
      const res = await fetch('/api/assist/voice', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: helpText }),
      });
      const data = await res.json().catch(() => ({}));
      const audioUrl = String(data?.audioUrl || '').trim();
      if (res.ok && audioUrl) {
        const a = new Audio(audioUrl);
        audioRef.current = a;
        a.onended = () => setPlaying(false);
        a.onerror = () => setPlaying(false);
        await a.play();
        setMsg('Playing premium voice guidance.');
        return;
      }

      if ('speechSynthesis' in window) {
        const u = new SpeechSynthesisUtterance(helpText);
        u.rate = 0.96;
        u.pitch = 1.0;
        u.volume = 0.9;
        u.onend = () => setPlaying(false);
        window.speechSynthesis.speak(u);
        setMsg('Using device voice guidance.');
        return;
      }

      setMsg('Voice unavailable. See text guidance below.');
      setPlaying(false);
    } catch {
      setMsg('Could not play voice right now. See text guidance below.');
      setPlaying(false);
    }
  }

  return (
    <div style={{ position: 'fixed', right: 14, bottom: 14, zIndex: 60 }}>
      <button
        onClick={() => setOpen((v) => !v)}
        style={{
          border: '1px solid rgba(56,189,248,.55)',
          background: nudge ? 'linear-gradient(180deg,#67e8f9,#22d3ee)' : 'linear-gradient(180deg,#38bdf8,#0ea5e9)',
          color: '#062437',
          borderRadius: 999,
          padding: '10px 14px',
          fontWeight: 800,
          boxShadow: '0 12px 24px rgba(14,165,233,.28)',
          cursor: 'pointer',
        }}
      >
        {nudge ? 'Need help? 👋' : 'AI Helper'}
      </button>

      {open ? (
        <div style={{ marginTop: 8, width: 320, maxWidth: 'calc(100vw - 28px)', border: '1px solid rgba(148,163,184,.3)', borderRadius: 14, background: 'linear-gradient(180deg, rgba(18,28,51,.95), rgba(15,23,42,.95))', color: '#e8eefc', padding: 12 }}>
          <div style={{ fontWeight: 800, marginBottom: 6 }}>AI-assisted helper</div>
          <div style={{ fontSize: 13, color: '#c7d8f8', lineHeight: 1.5 }}>{helpText}</div>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 10 }}>
            <button onClick={speak} disabled={playing} style={{ border: '1px solid #0284c7', background: 'linear-gradient(180deg,#38bdf8,#0ea5e9)', color: '#062437', borderRadius: 10, padding: '8px 10px', fontWeight: 800, cursor: 'pointer' }}>
              {playing ? 'Playing…' : 'Play voice guide'}
            </button>
            <button onClick={() => setOpen(false)} style={{ border: '1px solid rgba(148,163,184,.45)', background: 'rgba(15,23,42,.5)', color: '#dbe7ff', borderRadius: 10, padding: '8px 10px', fontWeight: 700, cursor: 'pointer' }}>
              Close
            </button>
          </div>
          {msg ? <div style={{ marginTop: 8, fontSize: 12, color: '#9fb2d6' }}>{msg}</div> : null}
        </div>
      ) : null}
    </div>
  );
}
