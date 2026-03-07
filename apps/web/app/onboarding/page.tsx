"use client";

import { useEffect, useMemo, useRef, useState } from 'react';
import AIAssistHelper from '../components/AIAssistHelper';

type Status = {
  connections: { x: boolean; linkedin: boolean; instagram: boolean; youtube: boolean };
  avatarComplete: boolean;
};

const STORY_SLIDES = [
  {
    eyebrow: 'CONTENT THAT STAYS FRESH',
    title: 'Never sound like the same brand twice',
    body: 'Every AI-assisted draft is grounded in Trend-to-Brand Intelligence or your own source content—so output stays relevant, timely, and distinct.',
    proof: 'Relevance first. Repetition last.',
    voiceover: 'Welcome to Demand Orchestrator, your AI-assisted content engine. Stay relevant, timely, and distinct in every post.',
  },
  {
    eyebrow: 'INTELLIGENCE + ORIGINALITY',
    title: 'Intelligence gives direction. Originality earns attention.',
    body: 'We use live trend signals to guide strategy, then diversify hooks, angles, and formats so your audience sees variety—not template fatigue.',
    proof: 'Strategic consistency, creative variation.',
    voiceover: 'We combine live demand signals with creative variation, so your brand stays consistent without sounding repetitive.',
  },
  {
    eyebrow: 'YOUR CONTENT, YOUR CONTROL',
    title: 'Bring your own content anytime',
    body: 'Start from your own video, image, script, or idea—or let DO generate from trend intelligence. You choose the source, we orchestrate the workflow.',
    proof: 'AI-assisted when useful. Human-led when preferred.',
    voiceover: 'Start from your own ideas, videos, or scripts—or generate with intelligence. You stay in control of every output.',
  },
  {
    eyebrow: 'FORMAT DIVERSITY, ONE STUDIO',
    title: 'One strategy. Multiple content experiences.',
    body: 'Publish avatar video, live-recorded video, uploaded assets, faceless creative, image posts, and text posts from one intuitive queue flow.',
    proof: 'Variety drives engagement. Simplicity drives execution.',
    voiceover: 'Run one strategy across avatar video, faceless creative, images, and text—from one clean studio workflow.',
  },
  {
    eyebrow: 'PERFORMANCE BRAIN',
    title: 'Your content learns what wins.',
    body: 'DemandOrchestrator tracks retention, shares, saves, clicks, and conversions per post—then automatically shifts the next content batch toward patterns your audience actually rewards.',
    proof: 'Publish → Measure → Score → Adapt.',
    voiceover: 'Every post teaches the system what works. Publish, measure, score, and adapt—so performance compounds over time.',
  },
];

const STEPS = [
  { title: 'Connect your channels', body: 'Link selected publishing channels once. After setup, connections stay in the background unless reconnect is needed.' },
  { title: 'Set publishing defaults', body: 'Confirm your timezone and workflow defaults so queue generation behaves predictably.' },
  { title: 'Create your avatar profile', body: 'Record or upload your 3–5 minute training clip to unlock premium video flows.' },
  { title: 'Launch studio mode', body: 'Everything is ready. Studio now stays focused on publishing, not setup.' },
];

export default function OnboardingPage() {
  const [phase, setPhase] = useState<'story' | 'setup'>('story');
  const [storyStep, setStoryStep] = useState(0);
  const [step, setStep] = useState(0);
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState<Status>({ connections: { x: false, linkedin: false, instagram: false, youtube: false }, avatarComplete: false });
  const [selectedPlatforms, setSelectedPlatforms] = useState<Array<'x'|'linkedin'|'instagram'|'youtube'>>(['x', 'linkedin']);
  const [defaultsConfirmed, setDefaultsConfirmed] = useState(false);
  const [brandSummary, setBrandSummary] = useState('');
  const [audienceSummary, setAudienceSummary] = useState('');
  const [offerSummary, setOfferSummary] = useState('');
  const [voiceSummary, setVoiceSummary] = useState('');
  const [doNotSay, setDoNotSay] = useState('');
  const [competitors, setCompetitors] = useState('');
  const [proofPoints, setProofPoints] = useState('');
  const [primaryGoal, setPrimaryGoal] = useState('lead_gen');
  const [defaultTimezone, setDefaultTimezone] = useState('America/New_York');
  const [defaultCadence, setDefaultCadence] = useState('weekdays');
  const [connectingPlatform, setConnectingPlatform] = useState('');
  const [devBypass, setDevBypass] = useState(false);
  const [autoPlayStory, setAutoPlayStory] = useState(false);
  const [voiceoverOn, setVoiceoverOn] = useState(true);
  const [premiumAudioBySlide, setPremiumAudioBySlide] = useState<string[]>([]);
  const [voiceoverDone, setVoiceoverDone] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  async function refreshStatus() {
    const res = await fetch('/api/onboarding/status', { cache: 'no-store' });
    const data = await res.json().catch(() => null);
    if (data) {
      setStatus({
        connections: data.connections || { x: false, linkedin: false, instagram: false, youtube: false },
        avatarComplete: Boolean(data.avatarComplete),
      });
    }
  }

  useEffect(() => {
    refreshStatus();
    if (typeof window !== 'undefined') {
      const q = new URLSearchParams(window.location.search);
      if (q.get('phase') === 'setup') setPhase('setup');
      if (q.get('dev') === '1') setDevBypass(true);
      const stepRaw = Number(q.get('step') || '0');
      if (Number.isFinite(stepRaw) && stepRaw >= 0 && stepRaw <= 3) setStep(stepRaw);
    }
  }, []);

  useEffect(() => {
    if (phase !== 'story') return;
    fetch('/api/onboarding/voiceover', { cache: 'no-store' })
      .then((r) => r.json())
      .then((data) => {
        const rows = Array.isArray(data?.audioBySlide) ? data.audioBySlide : [];
        setPremiumAudioBySlide(rows.map((x: any) => String(x.audioUrl || '')).filter(Boolean));
      })
      .catch(() => setPremiumAudioBySlide([]));
  }, [phase]);

  useEffect(() => {
    if (phase !== 'story' || !autoPlayStory || voiceoverOn || storyStep >= STORY_SLIDES.length - 1) return;
    const t = window.setTimeout(() => setStoryStep((s) => Math.min(s + 1, STORY_SLIDES.length - 1)), 9000);
    return () => window.clearTimeout(t);
  }, [phase, autoPlayStory, voiceoverOn, storyStep]);

  useEffect(() => {
    if (phase !== 'story' || !voiceoverOn || typeof window === 'undefined') return;
    const s = STORY_SLIDES[storyStep];
    if (!s) return;

    setVoiceoverDone(false);
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }
    if ('speechSynthesis' in window) window.speechSynthesis.cancel();

    const advanceIfNeeded = () => {
      setVoiceoverDone(true);
      if (autoPlayStory && storyStep < STORY_SLIDES.length - 1) {
        setStoryStep((curr) => Math.min(curr + 1, STORY_SLIDES.length - 1));
      }
    };

    const premiumAudio = premiumAudioBySlide[storyStep] || '';
    if (premiumAudio) {
      const a = new Audio(premiumAudio);
      a.preload = 'auto';
      a.onended = advanceIfNeeded;
      audioRef.current = a;
      a.play().catch(() => {
        if (!('speechSynthesis' in window)) return;
        const utterance = new SpeechSynthesisUtterance(s.voiceover || `${s.title}. ${s.body}`);
        utterance.rate = 0.95;
        utterance.pitch = 1.0;
        utterance.volume = 0.92;
        utterance.onend = () => advanceIfNeeded();
        const voices = window.speechSynthesis.getVoices();
        const preferred = voices.find((v) => /Samantha|Ava|Allison|Serena|Karen/i.test(v.name)) || voices.find((v) => /en-US|en_US/i.test(v.lang));
        if (preferred) utterance.voice = preferred;
        window.speechSynthesis.speak(utterance);
      });
      return () => {
        a.pause();
        a.onended = null;
      };
    }

    if (!('speechSynthesis' in window)) return;
    const utterance = new SpeechSynthesisUtterance(s.voiceover || `${s.title}. ${s.body}`);
    utterance.rate = 0.95;
    utterance.pitch = 1.0;
    utterance.volume = 0.92;
    utterance.onend = () => advanceIfNeeded();
    const voices = window.speechSynthesis.getVoices();
    const preferred = voices.find((v) => /Samantha|Ava|Allison|Serena|Karen/i.test(v.name)) || voices.find((v) => /en-US|en_US/i.test(v.lang));
    if (preferred) utterance.voice = preferred;
    window.speechSynthesis.speak(utterance);
    return () => window.speechSynthesis.cancel();
  }, [phase, storyStep, voiceoverOn, autoPlayStory, premiumAudioBySlide]);

  useEffect(() => {
    if (voiceoverOn || typeof window === 'undefined') return;
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }
    if ('speechSynthesis' in window) window.speechSynthesis.cancel();
    setVoiceoverDone(true);
  }, [voiceoverOn]);

  const allConnectionsReady = useMemo(() => {
    if (selectedPlatforms.length === 0) return true;
    return selectedPlatforms.every((p) => Boolean(status.connections[p]));
  }, [selectedPlatforms, status.connections]);

  async function markAvatarDone() {
    await fetch('/auth/complete-avatar-onboarding', { method: 'POST' });
    await refreshStatus();
  }

  async function complete() {
    setBusy(true);
    const res = await fetch('/auth/complete-onboarding', { method: 'POST' });
    setBusy(false);
    if (res.ok) window.location.href = '/studio';
  }

  const stepValid = devBypass ? true :
    step === 0 ? allConnectionsReady :
    step === 1
      ? defaultsConfirmed
        && defaultTimezone.trim().length >= 3
        && defaultCadence.trim().length >= 3
        && brandSummary.trim().length >= 12
        && audienceSummary.trim().length >= 12
        && offerSummary.trim().length >= 8
        && voiceSummary.trim().length >= 8
      : step === 2 ? status.avatarComplete : true;

  async function startOAuth(platform: 'x'|'linkedin'|'instagram'|'youtube') {
    setConnectingPlatform(platform);
    try {
      const res = await fetch('/api/onboarding/connect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ platform }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok || !data?.authUrl) {
        setConnectingPlatform('');
        return;
      }
      window.location.href = data.authUrl;
    } catch {
      setConnectingPlatform('');
    }
  }

  if (phase === 'story') {
    const s = STORY_SLIDES[storyStep];
    const storyLast = storyStep === STORY_SLIDES.length - 1;
    return (
      <main style={rootStyle}>
        <div style={cinemaOverlay} />
        <section style={{ ...heroCard, maxWidth: 980, minHeight: 420 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
            <div>
              <div style={{ fontSize: 12, letterSpacing: '.16em', opacity: 0.8 }}>{s.eyebrow}</div>
              <div style={{ marginTop: 6, fontSize: 11, letterSpacing: '.08em', textTransform: 'uppercase', color: '#a5f3fc' }}>AI-Assisted Content Engine Intro</div>
            </div>
            <button style={ghostBtn} onClick={() => { setAutoPlayStory(false); setVoiceoverOn(false); setStoryStep(STORY_SLIDES.length - 1); }}>Skip to Access</button>
          </div>

          <h2 style={{ margin: '0 0 10px', fontSize: 'clamp(1.8rem,5vw,3.2rem)', letterSpacing: '-.03em' }}>{s.title}</h2>
          <p style={{ color: '#d6e3ff', lineHeight: 1.75, fontSize: 18, maxWidth: 760 }}>{s.body}</p>
          <div style={{ marginTop: 14, fontSize: 13, letterSpacing: '.08em', textTransform: 'uppercase', color: '#7dd3fc' }}>{s.proof}</div>
          <div style={{ marginTop: 12, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            <span style={storyChip}>Trend-to-Brand intelligence</span>
            <span style={storyChip}>Multi-format publishing</span>
            <span style={storyChip}>Studio-first workflow</span>
          </div>

          <div style={{ width: '100%', height: 6, borderRadius: 999, background: 'rgba(148,163,184,.25)', overflow: 'hidden', margin: '20px 0 10px' }}>
            <div style={{ width: `${((storyStep + 1) / STORY_SLIDES.length) * 100}%`, height: '100%', background: 'linear-gradient(90deg,#38bdf8,#22d3ee)' }} />
          </div>
          <div style={{ fontSize: 12, color: '#9fb1d8', letterSpacing: '.06em', textTransform: 'uppercase' }}>Slide {storyStep + 1} of {STORY_SLIDES.length}</div>

          <div style={{ display: 'flex', gap: 10, marginTop: 16, flexWrap: 'wrap' }}>
            {storyStep > 0 ? <button style={secondaryBtn} onClick={() => { setAutoPlayStory(false); setStoryStep(storyStep - 1); }}>Back</button> : null}
            {!storyLast ? (
              <button style={primaryBtn} onClick={() => { setAutoPlayStory(false); setStoryStep(storyStep + 1); }}>Next</button>
            ) : (
              <>
                <button style={primaryBtn} onClick={() => { window.location.href = '/login'; }}>I have early access — enter now</button>
                <button style={secondaryBtn} onClick={() => { window.location.href = '/waitlist'; }}>No invite yet — join waitlist</button>
              </>
            )}
            {!storyLast ? <button style={ghostBtn} onClick={() => setAutoPlayStory((v) => !v)}>{autoPlayStory ? 'Autoplay: ON' : 'Autoplay: OFF'}</button> : null}
            {!storyLast ? <button style={ghostBtn} onClick={() => setVoiceoverOn((v) => !v)}>{voiceoverOn ? `VoiceOver: ON${premiumAudioBySlide.length ? ' (Premium)' : ''}` : 'VoiceOver: OFF'}</button> : null}
          </div>
          {!storyLast ? (
            <p style={{ marginTop: 10, color: '#9fb1d8', fontSize: 13 }}>
              {voiceoverOn
                ? (voiceoverDone ? 'Voiceover finished. Click Next when you’re ready.' : 'Voiceover is playing. Read at your own pace, then click Next.')
                : 'Read at your own pace, then click Next.'}
            </p>
          ) : null}
          {storyLast ? (
            <p style={{ marginTop: 10, color: '#9fb1d8', fontSize: 13 }}>
              Watch the vision. Then choose your path: instant access or waitlist.
            </p>
          ) : null}
        </section>
        <AIAssistHelper context="onboarding" stage={`story-${storyStep + 1}`} />
      </main>
    );
  }

  const current = STEPS[step];
  const isLast = step === STEPS.length - 1;

  return (
    <main style={rootStyle}>
      <div style={cinemaOverlay} />
      <section style={{ ...heroCard, maxWidth: 920 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
          <div style={{ fontSize: 12, letterSpacing: '.16em', opacity: 0.8 }}>ONBOARDING {step + 1} / {STEPS.length}</div>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <button style={ghostBtn} onClick={() => setDevBypass((v) => !v)}>{devBypass ? 'Developer Mode: ON' : 'Developer Mode'}</button>
            <div style={{ fontSize: 12, opacity: 0.8 }}>Premium Setup</div>
          </div>
        </div>

        <div style={{ width: '100%', height: 6, borderRadius: 999, background: 'rgba(148,163,184,.25)', overflow: 'hidden', marginBottom: 14 }}>
          <div style={{ width: `${((step + 1) / STEPS.length) * 100}%`, height: '100%', background: 'linear-gradient(90deg,#38bdf8,#22d3ee)' }} />
        </div>

        <h2 style={{ margin: '0 0 8px', fontSize: 'clamp(1.6rem,4vw,2.4rem)' }}>{current.title}</h2>
        <p style={{ color: '#c9d6f3', lineHeight: 1.7, marginTop: 0 }}>{current.body}</p>

        {step === 0 ? (
          <div style={panelStyle}>
            <div style={{ marginBottom: 8, fontWeight: 700 }}>Choose platforms for this onboarding</div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2,minmax(0,1fr))', gap: 8, marginBottom: 10 }}>
              {(['x', 'linkedin', 'instagram', 'youtube'] as const).map((p) => {
                const selected = selectedPlatforms.includes(p);
                const connected = Boolean(status.connections[p]);
                return (
                  <label key={p} style={{ padding: 8, borderRadius: 8, border: '1px solid rgba(148,163,184,.28)', display: 'flex', justifyContent: 'space-between', gap: 8, alignItems: 'center' }}>
                    <span style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                      <input
                        type="checkbox"
                        checked={selected}
                        onChange={(e) => {
                          const on = e.target.checked;
                          setSelectedPlatforms((prev) => {
                            if (on) return (prev.includes(p) ? prev : [...prev, p]);
                            return prev.filter((x) => x !== p);
                          });
                        }}
                      />
                      <b>{p.toUpperCase()}</b>
                    </span>
                    <span>{connected ? '✅' : selected ? '❌' : '⏭️'}</span>
                  </label>
                );
              })}
            </div>
            <div className="tiny" style={{ marginBottom: 8 }}>Selected platforms must be connected now. Unselected platforms can be added later.</div>
            <div style={{ marginTop: 10, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              {selectedPlatforms.map((p) => (
                <button key={p} onClick={() => startOAuth(p)} style={linkBtn} disabled={connectingPlatform.length > 0 && connectingPlatform !== p}>
                  {connectingPlatform === p ? `Connecting ${p.toUpperCase()}…` : `Connect ${p.toUpperCase()} via OAuth`}
                </button>
              ))}
              <button onClick={refreshStatus} style={secondaryBtn}>Refresh Status</button>
              <button onClick={() => { setSelectedPlatforms([]); setStep(1); }} style={secondaryBtn}>Skip for now</button>
            </div>
          </div>
        ) : null}

        {step === 1 ? (
          <div style={panelStyle}>
            <div style={{ marginBottom: 8, fontWeight: 700 }}>Brand intelligence profile (high-impact context)</div>
            <div className="tiny" style={{ marginBottom: 8 }}>This directly improves trend relevance, scripting quality, and originality.</div>

            <div style={{ display: 'grid', gap: 8, gridTemplateColumns: 'repeat(2,minmax(0,1fr))', marginBottom: 8 }}>
              <label>
                <div className="tiny" style={{ marginBottom: 4 }}>Default timezone</div>
                <input
                  value={defaultTimezone}
                  onChange={(e) => setDefaultTimezone(e.target.value)}
                  placeholder="America/New_York"
                  style={{ width: '100%', borderRadius: 10, border: '1px solid rgba(148,163,184,.35)', background: 'rgba(2,6,23,.5)', color: '#eaf0ff', padding: 10 }}
                />
              </label>
              <label>
                <div className="tiny" style={{ marginBottom: 4 }}>Default cadence</div>
                <select
                  value={defaultCadence}
                  onChange={(e) => setDefaultCadence(e.target.value)}
                  style={{ width: '100%', borderRadius: 10, border: '1px solid rgba(148,163,184,.35)', background: 'rgba(2,6,23,.5)', color: '#eaf0ff', padding: 10 }}
                >
                  <option value="weekdays">Weekdays</option>
                  <option value="daily">Daily</option>
                  <option value="three_weekly">3x Weekly</option>
                </select>
              </label>
            </div>

            <textarea
              value={brandSummary}
              onChange={(e) => setBrandSummary(e.target.value)}
              rows={3}
              placeholder="Brand purpose + category: What do you do, for whom, and why it matters?"
              style={{ width: '100%', borderRadius: 10, border: '1px solid rgba(148,163,184,.35)', background: 'rgba(2,6,23,.5)', color: '#eaf0ff', padding: 10, marginBottom: 8 }}
            />
            <textarea
              value={audienceSummary}
              onChange={(e) => setAudienceSummary(e.target.value)}
              rows={3}
              placeholder="Audience profile: ICP, pain points, objections, buying triggers"
              style={{ width: '100%', borderRadius: 10, border: '1px solid rgba(148,163,184,.35)', background: 'rgba(2,6,23,.5)', color: '#eaf0ff', padding: 10, marginBottom: 8 }}
            />
            <textarea
              value={offerSummary}
              onChange={(e) => setOfferSummary(e.target.value)}
              rows={2}
              placeholder="Core offer(s): products/services and strongest value proposition"
              style={{ width: '100%', borderRadius: 10, border: '1px solid rgba(148,163,184,.35)', background: 'rgba(2,6,23,.5)', color: '#eaf0ff', padding: 10, marginBottom: 8 }}
            />
            <textarea
              value={proofPoints}
              onChange={(e) => setProofPoints(e.target.value)}
              rows={2}
              placeholder="Proof points: case studies, outcomes, numbers, credentials"
              style={{ width: '100%', borderRadius: 10, border: '1px solid rgba(148,163,184,.35)', background: 'rgba(2,6,23,.5)', color: '#eaf0ff', padding: 10, marginBottom: 8 }}
            />
            <textarea
              value={competitors}
              onChange={(e) => setCompetitors(e.target.value)}
              rows={2}
              placeholder="Competitors/alternatives and how you differentiate"
              style={{ width: '100%', borderRadius: 10, border: '1px solid rgba(148,163,184,.35)', background: 'rgba(2,6,23,.5)', color: '#eaf0ff', padding: 10, marginBottom: 8 }}
            />
            <textarea
              value={voiceSummary}
              onChange={(e) => setVoiceSummary(e.target.value)}
              rows={2}
              placeholder="Brand voice + tone: e.g., authoritative, playful, contrarian, premium"
              style={{ width: '100%', borderRadius: 10, border: '1px solid rgba(148,163,184,.35)', background: 'rgba(2,6,23,.5)', color: '#eaf0ff', padding: 10, marginBottom: 8 }}
            />
            <textarea
              value={doNotSay}
              onChange={(e) => setDoNotSay(e.target.value)}
              rows={2}
              placeholder="Do-not-say list: compliance limits, prohibited claims, taboo phrases"
              style={{ width: '100%', borderRadius: 10, border: '1px solid rgba(148,163,184,.35)', background: 'rgba(2,6,23,.5)', color: '#eaf0ff', padding: 10, marginBottom: 8 }}
            />

            <label style={{ display: 'block', marginBottom: 10 }}>
              <div className="tiny" style={{ marginBottom: 4 }}>Primary account goal</div>
              <select
                value={primaryGoal}
                onChange={(e) => setPrimaryGoal(e.target.value)}
                style={{ width: '100%', borderRadius: 10, border: '1px solid rgba(148,163,184,.35)', background: 'rgba(2,6,23,.5)', color: '#eaf0ff', padding: 10 }}
              >
                <option value="lead_gen">Lead generation</option>
                <option value="brand_awareness">Brand awareness</option>
                <option value="education">Education / trust building</option>
                <option value="community">Community growth</option>
                <option value="sales_conversion">Sales conversion</option>
              </select>
            </label>

            <label style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              <input type="checkbox" checked={defaultsConfirmed} onChange={(e) => setDefaultsConfirmed(e.target.checked)} />
              I confirmed timezone, cadence, and default platform behavior.
            </label>
          </div>
        ) : null}

        {step === 2 ? (
          <div style={panelStyle}>
            <div style={{ marginBottom: 8 }}>Avatar setup: {status.avatarComplete ? '✅ complete' : '❌ incomplete'}</div>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              <a href="/studio/model-signup" style={linkBtn}>Open Avatar Recording</a>
              <button onClick={markAvatarDone} style={secondaryBtn}>I completed avatar setup</button>
            </div>
          </div>
        ) : null}

        <div style={{ display: 'flex', gap: 10, marginTop: 16, flexWrap: 'wrap' }}>
          {step > 0 ? <button style={secondaryBtn} onClick={() => setStep(step - 1)}>Back</button> : null}
          {!isLast ? (
            <button style={{ ...primaryBtn, opacity: stepValid ? 1 : 0.5 }} onClick={() => stepValid && setStep(step + 1)} disabled={!stepValid}>Next</button>
          ) : (
            <button style={{ ...primaryBtn, opacity: (devBypass || (allConnectionsReady && defaultsConfirmed && status.avatarComplete)) ? 1 : 0.5 }} disabled={busy || !(devBypass || (allConnectionsReady && defaultsConfirmed && status.avatarComplete))} onClick={complete}>{busy ? 'Launching…' : 'Enter Studio'}</button>
          )}
        </div>
      </section>
      <AIAssistHelper context="onboarding" stage={`setup-${step + 1}`} />
    </main>
  );
}

const rootStyle: React.CSSProperties = {
  minHeight: '100vh',
  background: 'radial-gradient(900px 500px at 0% -10%, rgba(56,189,248,.18), transparent 60%), radial-gradient(900px 500px at 100% 0%, rgba(59,130,246,.16), transparent 60%), #060b16',
  color: '#eaf0ff',
  fontFamily: 'Inter, system-ui',
  position: 'relative',
  overflow: 'hidden',
  display: 'grid',
  placeItems: 'center',
  padding: 24,
};

const cinemaOverlay: React.CSSProperties = {
  position: 'absolute', inset: 0,
  backgroundImage: 'linear-gradient(rgba(148,163,184,.05) 1px, transparent 1px), linear-gradient(90deg, rgba(148,163,184,.05) 1px, transparent 1px)',
  backgroundSize: '34px 34px',
  maskImage: 'radial-gradient(circle at 50% 30%, black 35%, transparent 82%)',
  pointerEvents: 'none',
};

const heroCard: React.CSSProperties = {
  width: '100%', maxWidth: 980,
  border: '1px solid rgba(148,163,184,.26)', borderRadius: 20, padding: 28,
  background: 'linear-gradient(180deg, rgba(18,28,51,.86), rgba(12,18,32,.8))',
  boxShadow: '0 30px 80px rgba(2,6,23,.5)', position: 'relative', zIndex: 1,
};

const panelStyle: React.CSSProperties = {
  border: '1px solid rgba(148,163,184,.26)', borderRadius: 12, padding: 12, background: 'rgba(15,23,42,.45)', marginTop: 8,
};

const primaryBtn: React.CSSProperties = {
  background: 'linear-gradient(180deg,#38bdf8,#0ea5e9)', border: '1px solid #0284c7', color: '#062437', borderRadius: 10, padding: '10px 14px', fontWeight: 800, cursor: 'pointer',
};

const secondaryBtn: React.CSSProperties = {
  background: 'rgba(15,23,42,.65)', border: '1px solid rgba(148,163,184,.35)', color: '#e8eefc', borderRadius: 10, padding: '10px 14px', fontWeight: 700, cursor: 'pointer',
};

const linkBtn: React.CSSProperties = {
  display: 'inline-block', textDecoration: 'none',
  background: 'linear-gradient(180deg,#38bdf8,#0ea5e9)', border: '1px solid #0284c7', color: '#062437', borderRadius: 10, padding: '10px 14px', fontWeight: 800,
};

const ghostBtn: React.CSSProperties = {
  background: 'transparent',
  border: '1px solid rgba(148,163,184,.35)',
  color: '#cfe1ff',
  borderRadius: 999,
  padding: '7px 12px',
  fontWeight: 700,
  cursor: 'pointer',
};

const storyChip: React.CSSProperties = {
  border: '1px solid rgba(125,211,252,.35)',
  borderRadius: 999,
  padding: '6px 10px',
  fontSize: 11,
  letterSpacing: '.04em',
  textTransform: 'uppercase',
  color: '#d6ecff',
  background: 'rgba(14,165,233,.14)',
};
