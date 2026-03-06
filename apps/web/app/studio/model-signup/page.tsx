"use client";

import Link from 'next/link';
import { useEffect, useMemo, useRef, useState } from 'react';

const DEFAULT_SCRIPT = `Hi, I’m [Name].
I’m recording this video to create my AI avatar for DemandOrchestrator.

I help [audience] with [problem].
Most people struggle with [pain point], and the biggest reason is [reason].

Here’s what usually works best:

First, focus on one clear goal at a time.
Second, simplify your message so it’s easy to act on.
Third, measure what’s working and repeat it consistently.

A quick example:
Last month, we tested a small change in messaging.
We made the opening line clearer, added one concrete takeaway, and used a direct call to action.
That one adjustment improved engagement and made follow-up conversations easier.

If you’re trying to improve results, start with clarity.
Say what changed, why it matters, and what someone should do next.

For content, consistency beats intensity.
Short, clear, useful posts outperform complicated content most of the time.
The key is to stay relevant to what your audience cares about right now.

Thanks for watching.
I’m excited to use this avatar to create helpful, consistent content.`;

function estimateMinutes(wordCount: number) {
  // conservative pace for clear avatar capture
  return wordCount / 130;
}

export default function ModelSignupPage() {
  const [script, setScript] = useState(DEFAULT_SCRIPT);
  const [cameraOn, setCameraOn] = useState(false);
  const [cameraError, setCameraError] = useState('');
  const [cameraWarning, setCameraWarning] = useState('');
  const [teleprompterOn, setTeleprompterOn] = useState(true);
  const [promptRolling, setPromptRolling] = useState(false);
  const [countdown, setCountdown] = useState(0);
  const [scrollSpeed, setScrollSpeed] = useState(20);
  const [uploadDragOver, setUploadDragOver] = useState(false);
  const [uploadedFileName, setUploadedFileName] = useState('');
  const [uploadedVideoUrl, setUploadedVideoUrl] = useState('');
  const [consentFileName, setConsentFileName] = useState('');
  const [consentUploadBusy, setConsentUploadBusy] = useState(false);
  const [uploadValidation, setUploadValidation] = useState<Array<{ label: string; ok: boolean; detail?: string }>>([]);
  const [avatarDisplayName, setAvatarDisplayName] = useState('My Avatar');
  const [avatarEmail, setAvatarEmail] = useState('');
  const [avatarFullName, setAvatarFullName] = useState('');
  const [trainingFootageUrl, setTrainingFootageUrl] = useState('');
  const [consentVideoUrl, setConsentVideoUrl] = useState('');
  const [avatarProfileId, setAvatarProfileId] = useState('');
  const [providerAvatarId, setProviderAvatarId] = useState('');
  const [providerStatus, setProviderStatus] = useState('');
  const [avatarBusy, setAvatarBusy] = useState(false);
  const [avatarStatus, setAvatarStatus] = useState('');
  const [cameraDevices, setCameraDevices] = useState<Array<{ deviceId: string; label: string }>>([]);
  const [noCameraDetected, setNoCameraDetected] = useState(false);
  const [selectedCameraId, setSelectedCameraId] = useState('');
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const promptRef = useRef<HTMLDivElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const words = useMemo(() => script.trim().split(/\s+/).filter(Boolean).length, [script]);
  const minutes = useMemo(() => estimateMinutes(words), [words]);

  useEffect(() => {
    if (!teleprompterOn || !cameraOn || !promptRolling || !promptRef.current) return;
    const el = promptRef.current;
    const id = setInterval(() => {
      if (!promptRef.current) return;
      el.scrollTop = Math.min(el.scrollTop + scrollSpeed / 20, el.scrollHeight);
    }, 50);
    return () => clearInterval(id);
  }, [teleprompterOn, cameraOn, promptRolling, scrollSpeed, script]);

  useEffect(() => {
    async function loadDevices() {
      try {
        const devices = await navigator.mediaDevices.enumerateDevices();
        const cams = devices
          .filter((d) => d.kind === 'videoinput')
          .map((d, i) => ({ deviceId: d.deviceId, label: d.label || `Camera ${i + 1}` }));
        setCameraDevices(cams);
        setNoCameraDetected(cams.length === 0);
        if (!selectedCameraId && cams[0]?.deviceId) setSelectedCameraId(cams[0].deviceId);
      } catch {}
    }
    loadDevices();
  }, [selectedCameraId]);

  useEffect(() => {
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((t) => t.stop());
        streamRef.current = null;
      }
      if (uploadedVideoUrl) URL.revokeObjectURL(uploadedVideoUrl);
    };
  }, [uploadedVideoUrl]);

  async function startCamera() {
    setCameraError('');
    setCameraWarning('');
    setPromptRolling(false);
    setCountdown(0);

    if (noCameraDetected) {
      setCameraError('No camera detected on this device. Use upload flow or connect a webcam.');
      return;
    }

    if (!navigator?.mediaDevices?.getUserMedia) {
      setCameraError('Camera API unavailable in this browser/session.');
      return;
    }

    try {
      const baseVideo = { width: { ideal: 1280 }, height: { ideal: 720 } } as MediaTrackConstraints;
      let stream: MediaStream | null = null;

      try {
        stream = await navigator.mediaDevices.getUserMedia({
          video: selectedCameraId ? { ...baseVideo, deviceId: { exact: selectedCameraId } } : { ...baseVideo, facingMode: 'user' },
          audio: true,
        });
      } catch {
        try {
          // Fallback when saved device id is stale.
          stream = await navigator.mediaDevices.getUserMedia({
            video: { ...baseVideo, facingMode: 'user' },
            audio: true,
          });
        } catch {
          // Last fallback: video only if mic permission/availability fails.
          stream = await navigator.mediaDevices.getUserMedia({
            video: { ...baseVideo, facingMode: 'user' },
            audio: false,
          });
          setCameraWarning('Camera started without microphone. Check mic permissions before final recording.');
        }
      }

      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
      setCameraOn(true);

      setCountdown(3);
      const interval = window.setInterval(() => {
        setCountdown((prev) => {
          if (prev <= 1) {
            window.clearInterval(interval);
            setPromptRolling(true);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    } catch (e: any) {
      const msg = e?.name ? `${e.name}: ${e?.message || 'Could not access camera/microphone'}` : (e?.message || 'Could not access camera/microphone');
      setCameraError(msg);
      setCameraOn(false);
      setPromptRolling(false);
      setCountdown(0);
    }
  }

  function stopCamera() {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
    if (videoRef.current) videoRef.current.srcObject = null;
    setCameraOn(false);
    setPromptRolling(false);
    setCountdown(0);
  }

  function validateUploadedVideo(file: File, meta: { duration: number; width: number; height: number }) {
    const rules = [
      {
        label: 'Duration is 3–5 minutes (minimum 2 minutes)',
        ok: meta.duration >= 120 && meta.duration <= 360,
        detail: `${Math.round(meta.duration)}s detected`,
      },
      {
        label: 'Resolution is at least 720p',
        ok: meta.width >= 1280 && meta.height >= 720,
        detail: `${meta.width}x${meta.height}`,
      },
      {
        label: 'Format is supported (mp4/mov/webm)',
        ok: /video\/(mp4|quicktime|webm)/i.test(file.type) || /\.(mp4|mov|webm)$/i.test(file.name),
        detail: file.type || file.name,
      },
      {
        label: 'File size under 1GB',
        ok: file.size <= 1024 * 1024 * 1024,
        detail: `${(file.size / (1024 * 1024)).toFixed(1)} MB`,
      },
    ];
    setUploadValidation(rules);
  }

  async function uploadFileForAvatar(file: File) {
    const form = new FormData();
    form.append('file', file);
    const res = await fetch('/api/avatar/upload', { method: 'POST', body: form });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data?.detail || 'upload failed');
    return String(data?.url || '');
  }

  async function handleVideoFile(file: File | null) {
    if (!file) return;
    if (uploadedVideoUrl) URL.revokeObjectURL(uploadedVideoUrl);
    const url = URL.createObjectURL(file);
    setUploadedVideoUrl(url);
    setUploadedFileName(file.name);

    const v = document.createElement('video');
    v.preload = 'metadata';
    v.src = url;
    await new Promise<void>((resolve) => {
      v.onloadedmetadata = () => resolve();
      v.onerror = () => resolve();
    });

    validateUploadedVideo(file, {
      duration: Number.isFinite(v.duration) ? v.duration : 0,
      width: v.videoWidth || 0,
      height: v.videoHeight || 0,
    });

    try {
      const publicUrl = await uploadFileForAvatar(file);
      setTrainingFootageUrl(publicUrl);
    } catch (e: any) {
      setAvatarStatus(`Training video upload failed: ${e?.message || 'upload failed'}`);
    }
  }

  async function handleConsentFile(file: File | null) {
    if (!file) return;
    setConsentFileName(file.name);
    setConsentUploadBusy(true);
    try {
      const publicUrl = await uploadFileForAvatar(file);
      setConsentVideoUrl(publicUrl);
    } catch (e: any) {
      setAvatarStatus(`Consent video upload failed: ${e?.message || 'upload failed'}`);
    } finally {
      setConsentUploadBusy(false);
    }
  }

  async function createHeyGenAvatar() {
    setAvatarStatus('');
    if (!avatarFullName.trim() || !avatarEmail.trim() || !trainingFootageUrl.trim() || !consentVideoUrl.trim()) {
      setAvatarStatus('Please enter full name, email, training footage URL, and consent video URL.');
      return;
    }

    const workspaceId = (typeof document !== 'undefined'
      ? (document.cookie.match(/(?:^|; )do_workspace_id=([^;]+)/)?.[1] || 'default')
      : 'default');

    setAvatarBusy(true);
    const res = await fetch('/api/avatar/heygen/create', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        workspaceId: decodeURIComponent(workspaceId),
        fullName: avatarFullName,
        email: avatarEmail,
        avatarName: avatarDisplayName,
        trainingFootageUrl,
        consentVideoUrl,
      }),
    });
    const data = await res.json().catch(() => ({}));
    setAvatarBusy(false);
    if (!res.ok) {
      setAvatarStatus(data?.detail || 'Failed to create avatar job.');
      return;
    }
    setAvatarProfileId(data?.avatarProfileId || '');
    setProviderAvatarId(data?.providerAvatarId || '');
    setProviderStatus(data?.providerStatus || 'in_progress');
    setAvatarStatus('Avatar job submitted. Use Refresh Status until it shows complete.');
  }

  async function refreshHeyGenAvatar() {
    if (!avatarProfileId) {
      setAvatarStatus('Create avatar first so we have a profile to refresh.');
      return;
    }
    setAvatarBusy(true);
    const res = await fetch('/api/avatar/heygen/refresh', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ avatarProfileId }),
    });
    const data = await res.json().catch(() => ({}));
    setAvatarBusy(false);
    if (!res.ok) {
      setAvatarStatus(data?.detail || 'Failed to refresh avatar status.');
      return;
    }
    setProviderStatus(data?.providerStatus || 'unknown');
    setAvatarStatus(data?.status === 'active'
      ? 'Avatar is complete and active in your avatar database.'
      : `Avatar still processing (${data?.providerStatus || 'pending'}).`);
  }

  const uploadPass = uploadValidation.length > 0 && uploadValidation.every((r) => r.ok);

  return (
    <main style={{ minHeight: '100vh', background: '#0b1220', color: '#e8eefc', padding: 24 }}>
      <div style={{ maxWidth: 1120, margin: '0 auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 18 }}>
          <h1 style={{ margin: 0, fontSize: 34, letterSpacing: '-.02em' }}>Avatar Recording Studio</h1>
          <Link href="/studio" style={{ color: '#c5d3f8' }}>← Back to Studio</Link>
        </div>

        <p style={{ color: '#a5b4d4', marginTop: 0 }}>
          Record a clean 3–5 minute training video once. Keep your eyes front-and-center using the built-in teleprompter overlay.
        </p>

        <section style={{ border: '1px solid rgba(148,163,184,.3)', borderRadius: 14, padding: 16, background: 'rgba(18,28,51,.75)', marginBottom: 12 }}>
          <h2 style={{ marginTop: 0 }}>Recording checklist (required)</h2>
          <ul style={{ margin: 0, paddingLeft: 18, color: '#c7d2ee', lineHeight: 1.7 }}>
            <li>3–5 minutes, one continuous take (no cuts)</li>
            <li>Eye-level framing (head + upper torso), look into camera</li>
            <li>Quiet room, clear voice, no music/background TV</li>
            <li>Soft front lighting, no strong backlight</li>
            <li>Solid-color clothing, avoid busy patterns/logos</li>
          </ul>
        </section>

        {noCameraDetected ? (
          <section style={{ border: '1px solid rgba(251,113,133,.55)', borderRadius: 14, padding: 14, background: 'rgba(127,29,29,.25)', marginBottom: 12 }}>
            <b>No camera detected on this device.</b>
            <div style={{ marginTop: 4, color: '#fecdd3', fontSize: 13 }}>
              Connect a webcam or continue with the upload flow below (recommended on headless machines).
            </div>
          </section>
        ) : null}

        <section style={{ border: '1px solid rgba(148,163,184,.3)', borderRadius: 14, padding: 16, background: 'rgba(18,28,51,.75)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8, gap: 8, flexWrap: 'wrap' }}>
            <h2 style={{ margin: 0 }}>Camera + teleprompter</h2>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              <span style={{ fontSize: 12, color: '#a5b4d4' }}>{words} words · ~{minutes.toFixed(1)} min</span>
              <button type="button" onClick={() => setScript(DEFAULT_SCRIPT)} style={btnSecondary}>Use default script</button>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 12 }}>
            <div style={{ position: 'relative', borderRadius: 12, overflow: 'hidden', border: '1px solid rgba(148,163,184,.35)', background: '#0a1020', minHeight: 420 }}>
              <video ref={videoRef} playsInline muted style={{ width: '100%', height: '100%', objectFit: 'cover', transform: 'scaleX(-1)' }} />
              {!cameraOn ? (
                <div style={{ position: 'absolute', inset: 0, display: 'grid', placeItems: 'center', color: '#9fb2d6', textAlign: 'center', padding: 16 }}>
                  <div>
                    <div style={{ marginBottom: 8 }}>Camera preview will appear here</div>
                    <button type="button" style={btnPrimary} onClick={startCamera}>Start Camera Preview</button>
                    {cameraError ? <div style={{ marginTop: 8, color: '#fca5a5' }}>{cameraError}</div> : null}
                    {cameraWarning ? <div style={{ marginTop: 8, color: '#fcd34d' }}>{cameraWarning}</div> : null}
                  </div>
                </div>
              ) : null}

              {teleprompterOn ? (
                <div style={{ position: 'absolute', left: '12%', right: '12%', top: '12%', bottom: '12%', pointerEvents: 'none' }}>
                  <div ref={promptRef} style={{ height: '100%', overflowY: 'auto', padding: 18, borderRadius: 10, background: 'rgba(2,6,23,.42)', border: '1px solid rgba(148,163,184,.32)' }}>
                    <div style={{ fontSize: 34, lineHeight: 1.5, color: '#f8fbff', textShadow: '0 2px 8px rgba(0,0,0,.75)' }}>
                      {script}
                    </div>
                  </div>
                </div>
              ) : null}

              <div style={{ position: 'absolute', top: '8%', left: '50%', transform: 'translateX(-50%)', width: 10, height: 10, borderRadius: 999, background: 'rgba(56,189,248,.95)', boxShadow: '0 0 8px rgba(56,189,248,.85)' }} />

              {countdown > 0 ? (
                <div style={{ position: 'absolute', inset: 0, display: 'grid', placeItems: 'center', background: 'rgba(2,6,23,.32)', color: '#eaf6ff', fontSize: 72, fontWeight: 800, textShadow: '0 0 20px rgba(56,189,248,.7)' }}>
                  {countdown}
                </div>
              ) : null}
            </div>

            <div>
              <textarea
                value={script}
                onChange={(e) => setScript(e.target.value)}
                rows={18}
                style={{ ...inputStyle, width: '100%', lineHeight: 1.45 }}
              />
              <div style={{ display: 'grid', gap: 8, marginTop: 8 }}>
                <label style={{ fontSize: 13, color: '#c7d2ee' }}>
                  Camera source
                  <select
                    value={selectedCameraId}
                    onChange={(e) => setSelectedCameraId(e.target.value)}
                    style={{ ...inputStyle, width: '100%', marginTop: 4 }}
                  >
                    {cameraDevices.length === 0 ? <option value="">Default camera</option> : null}
                    {cameraDevices.map((c) => (
                      <option key={c.deviceId} value={c.deviceId}>{c.label}</option>
                    ))}
                  </select>
                </label>

                <label style={{ fontSize: 13, color: '#c7d2ee', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span>Teleprompter overlay</span>
                  <input type="checkbox" checked={teleprompterOn} onChange={(e) => setTeleprompterOn(e.target.checked)} />
                </label>
                <div style={{ fontSize: 12, color: '#9fb2d6' }}>
                  {cameraOn ? (countdown > 0 ? `Starting in ${countdown}…` : (promptRolling ? 'Teleprompter rolling.' : 'Teleprompter paused.')) : 'Start camera to begin teleprompter countdown.'}
                </div>
                <label style={{ fontSize: 13, color: '#c7d2ee' }}>
                  Scroll speed: {scrollSpeed}
                  <input type="range" min={6} max={45} value={scrollSpeed} onChange={(e) => setScrollSpeed(Number(e.target.value))} style={{ width: '100%' }} />
                </label>
                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                  <button type="button" onClick={() => setScrollSpeed(12)} style={btnSecondary}>Slow</button>
                  <button type="button" onClick={() => setScrollSpeed(20)} style={btnSecondary}>Normal</button>
                  <button type="button" onClick={() => setScrollSpeed(32)} style={btnSecondary}>Fast</button>
                </div>
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                  {!cameraOn ? (
                    <button type="button" onClick={startCamera} style={btnPrimary}>Start Camera</button>
                  ) : (
                    <>
                      <button type="button" onClick={stopCamera} style={btnSecondary}>Stop Camera</button>
                      <button type="button" onClick={() => setPromptRolling((v) => !v)} style={btnSecondary}>
                        {promptRolling ? 'Pause Teleprompter' : 'Resume Teleprompter'}
                      </button>
                    </>
                  )}
                </div>

                <div
                  onDragOver={(e) => { e.preventDefault(); setUploadDragOver(true); }}
                  onDragLeave={() => setUploadDragOver(false)}
                  onDrop={(e) => {
                    e.preventDefault();
                    setUploadDragOver(false);
                    const f = e.dataTransfer.files?.[0] || null;
                    handleVideoFile(f);
                  }}
                  style={{
                    marginTop: 10,
                    padding: 12,
                    borderRadius: 10,
                    border: uploadDragOver ? '1px solid #67e8f9' : '1px dashed rgba(148,163,184,.45)',
                    background: uploadDragOver ? 'rgba(56,189,248,.12)' : 'rgba(15,23,42,.35)',
                  }}
                >
                  <div style={{ fontWeight: 700, marginBottom: 6 }}>Upload your 3–5 minute training video</div>
                  <div style={{ fontSize: 12, color: '#a5b4d4', marginBottom: 8 }}>
                    Drag & drop from hard drive/USB, or choose file manually. We auto-upload and generate the URL behind the scenes.
                  </div>
                  <input
                    type="file"
                    accept="video/mp4,video/quicktime,video/webm,.mp4,.mov,.webm"
                    onChange={(e) => handleVideoFile(e.target.files?.[0] || null)}
                  />
                  {uploadedFileName ? <div style={{ marginTop: 8, fontSize: 12 }}>Training file: {uploadedFileName}</div> : null}

                  <div style={{ marginTop: 10, fontWeight: 700, marginBottom: 6 }}>Upload consent statement video</div>
                  <div style={{ fontSize: 12, color: '#a5b4d4', marginBottom: 8 }}>
                    This is the explicit consent clip. We auto-upload and link it to avatar creation.
                  </div>
                  <input
                    type="file"
                    accept="video/mp4,video/quicktime,video/webm,.mp4,.mov,.webm"
                    onChange={(e) => handleConsentFile(e.target.files?.[0] || null)}
                  />
                  {consentFileName ? <div style={{ marginTop: 8, fontSize: 12 }}>Consent file: {consentFileName} {consentUploadBusy ? '(uploading...)' : ''}</div> : null}
                </div>

                {uploadedVideoUrl ? (
                  <video controls src={uploadedVideoUrl} style={{ width: '100%', marginTop: 10, borderRadius: 10, border: '1px solid rgba(148,163,184,.35)' }} />
                ) : null}

                {uploadValidation.length > 0 ? (
                  <div style={{ marginTop: 10, border: '1px solid rgba(148,163,184,.35)', borderRadius: 10, padding: 10 }}>
                    <div style={{ fontWeight: 700, marginBottom: 6 }}>Upload quality check</div>
                    <ul style={{ margin: 0, paddingLeft: 18, fontSize: 13, lineHeight: 1.6 }}>
                      {uploadValidation.map((r) => (
                        <li key={r.label} style={{ color: r.ok ? '#86efac' : '#fca5a5' }}>
                          {r.ok ? '✅' : '❌'} {r.label} <span style={{ color: '#a5b4d4' }}>({r.detail})</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : null}

                <div style={{ marginTop: 10, border: '1px solid rgba(148,163,184,.35)', borderRadius: 10, padding: 10 }}>
                  <div style={{ fontWeight: 700, marginBottom: 6 }}>Create Avatar + Auto-save to Avatar Database</div>
                  <div style={{ fontSize: 12, color: '#a5b4d4', marginBottom: 8 }}>
                    Upload videos above. We auto-populate secure file links behind the scenes, submit avatar creation, then activate it in your avatar database.
                  </div>
                  <input value={avatarFullName} onChange={(e) => setAvatarFullName(e.target.value)} placeholder="Full name" style={{ ...inputStyle, width: '100%', marginBottom: 8 }} />
                  <input value={avatarEmail} onChange={(e) => setAvatarEmail(e.target.value)} placeholder="Email" style={{ ...inputStyle, width: '100%', marginBottom: 8 }} />
                  <input value={avatarDisplayName} onChange={(e) => setAvatarDisplayName(e.target.value)} placeholder="Avatar display name" style={{ ...inputStyle, width: '100%', marginBottom: 8 }} />
                  <div style={{ fontSize: 12, color: '#9fb2d6', marginBottom: 8 }}>
                    Training URL: {trainingFootageUrl ? '✅ auto-generated' : '⏳ waiting for upload'} · Consent URL: {consentVideoUrl ? '✅ auto-generated' : '⏳ waiting for upload'}
                  </div>
                  <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                    <button type="button" onClick={createHeyGenAvatar} style={{ ...btnPrimary, opacity: avatarBusy ? 0.7 : 1 }} disabled={avatarBusy || !trainingFootageUrl || !consentVideoUrl}>
                      {avatarBusy ? 'Submitting…' : 'Create Avatar'}
                    </button>
                    <button type="button" onClick={refreshHeyGenAvatar} style={btnSecondary} disabled={avatarBusy || !avatarProfileId}>
                      Refresh Status
                    </button>
                  </div>
                  {(avatarProfileId || providerAvatarId || providerStatus) ? (
                    <div style={{ marginTop: 8, fontSize: 12, color: '#c7d2ee' }}>
                      Profile: {avatarProfileId || '—'} · Provider Avatar: {providerAvatarId || '—'} · Provider Status: {providerStatus || '—'}
                    </div>
                  ) : null}
                  {avatarStatus ? <div style={{ marginTop: 8, fontSize: 12, color: avatarStatus.toLowerCase().includes('active') ? '#86efac' : '#fca5a5' }}>{avatarStatus}</div> : null}
                </div>
              </div>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}

const inputStyle: React.CSSProperties = {
  border: '1px solid rgba(148,163,184,.35)',
  borderRadius: 10,
  padding: '10px 12px',
  background: 'rgba(15,23,42,.55)',
  color: '#e8eefc',
};

const btnPrimary: React.CSSProperties = {
  background: 'linear-gradient(180deg,#38bdf8,#0ea5e9)',
  border: '1px solid #0284c7',
  color: '#062437',
  borderRadius: 10,
  padding: '10px 12px',
  fontWeight: 800,
};

const btnSecondary: React.CSSProperties = {
  background: 'rgba(15,23,42,.65)',
  border: '1px solid rgba(148,163,184,.35)',
  color: '#e8eefc',
  borderRadius: 10,
  padding: '8px 10px',
  fontWeight: 600,
};
