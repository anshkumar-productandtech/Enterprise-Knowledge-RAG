import { backendFetch, clientIp, messageForStatus } from "@/lib/backend";

export const dynamic = "force-dynamic";

export async function POST(req: Request) {
  let body: { question?: unknown; role?: unknown };
  try {
    body = await req.json();
  } catch {
    return Response.json({ message: messageForStatus(400) }, { status: 400 });
  }
  if (typeof body.question !== "string" || typeof body.role !== "string") {
    return Response.json({ message: messageForStatus(400) }, { status: 400 });
  }

  let upstream: Response;
  try {
    upstream = await backendFetch("/chat", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ question: body.question, role: body.role }),
      clientIp: clientIp(req),
    });
  } catch {
    return Response.json({ message: messageForStatus(502) }, { status: 502 });
  }

  if (!upstream.ok || !upstream.body) {
    return Response.json({ message: messageForStatus(upstream.status) }, { status: upstream.status });
  }
  return new Response(upstream.body, {
    headers: {
      "content-type": "text/event-stream; charset=utf-8",
      "cache-control": "no-cache, no-transform",
    },
  });
}
