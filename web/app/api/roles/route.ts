import { backendFetch, messageForStatus } from "@/lib/backend";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const upstream = await backendFetch("/roles");
    if (!upstream.ok) {
      return Response.json({ message: messageForStatus(upstream.status) }, { status: 502 });
    }
    return Response.json(await upstream.json());
  } catch {
    return Response.json({ message: messageForStatus(502) }, { status: 502 });
  }
}
