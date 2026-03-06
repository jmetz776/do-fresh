import { NextResponse } from 'next/server';
import { mkdir, writeFile } from 'fs/promises';
import path from 'path';

export async function POST(req: Request) {
  try {
    const form = await req.formData();
    const file = form.get('file');
    if (!(file instanceof File)) {
      return NextResponse.json({ detail: 'file is required' }, { status: 400 });
    }

    const bytes = Buffer.from(await file.arrayBuffer());
    const safeName = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}-${file.name.replace(/[^a-zA-Z0-9._-]/g, '_')}`;
    const relDir = path.join('public', 'avatar-uploads');
    const absDir = path.join(process.cwd(), relDir);
    await mkdir(absDir, { recursive: true });

    const absFile = path.join(absDir, safeName);
    await writeFile(absFile, bytes);

    const url = new URL(req.url);
    const publicUrl = `${url.protocol}//${url.host}/avatar-uploads/${safeName}`;
    return NextResponse.json({ ok: true, url: publicUrl, name: safeName });
  } catch (e: any) {
    return NextResponse.json({ detail: e?.message || 'upload failed' }, { status: 500 });
  }
}
