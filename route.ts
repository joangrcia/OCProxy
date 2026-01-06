import { NextRequest } from 'next/server';

export const runtime = 'edge';

export async function POST(req: NextRequest) {
  const body = await req.json();
  const apiKey = req.headers.get('Authorization') || `Bearer ${process.env.NVIDIA_API_KEY}`;

  // Pastikan extra_body untuk thinking aktif jika belum ada
  if (!body.extra_body) {
    body.extra_body = { chat_template_kwargs: { thinking: true } };
  }

  const response = await fetch('https://integrate.api.nvidia.com/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': apiKey,
    },
    body: JSON.stringify(body),
  });

  // Jika tidak streaming, langsung kembalikan
  if (!body.stream) {
    return response;
  }

  // Transform Stream untuk memastikan reasoning terkirim dengan benar
  const encoder = new TextEncoder();
  const decoder = new TextDecoder();

  const stream = new ReadableStream({
    async start(controller) {
      const reader = response.body?.getReader();
      if (!reader) return;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        // Teruskan chunk apa adanya ke OpenCode
        controller.enqueue(encoder.encode(chunk));
      }
      controller.close();
    },
  });

  return new Response(stream, {
    headers: { 'Content-Type': 'text/event-stream' },
  });
}
