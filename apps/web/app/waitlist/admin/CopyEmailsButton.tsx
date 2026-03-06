'use client';

import { useState } from 'react';

export default function CopyEmailsButton({ emails }: { emails: string[] }) {
  const [copied, setCopied] = useState(false);

  async function onCopy() {
    const payload = emails.join(', ');
    await navigator.clipboard.writeText(payload);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  return (
    <button type="button" onClick={onCopy} disabled={!emails.length}>
      {copied ? 'Copied' : `Copy ${emails.length} emails`}
    </button>
  );
}
