const HOP_HEADERS = new Set(["host", "connection", "content-length", "transfer-encoding", "accept-encoding", "expect"]);

type Context = { params: { path: string[] } };

async function proxy(request: Request, context: Context) {
  const base = (process.env.API_INTERNAL_URL || "http://127.0.0.1:8000").replace(/\/$/, "");
  const incoming = new URL(request.url);
  const target = `${base}/${context.params.path.join("/")}${incoming.search}`;
  const headers = new Headers(request.headers);
  HOP_HEADERS.forEach((key) => headers.delete(key));
  const method = request.method.toUpperCase();
  const body = method === "GET" || method === "HEAD" ? undefined : await request.arrayBuffer();
  const response = await fetch(target, { method, headers, body, cache: "no-store", redirect: "manual" });
  const outgoing = new Headers();
  response.headers.forEach((value, key) => {
    if (!["content-encoding", "transfer-encoding", "content-length", "connection"].includes(key)) {
      outgoing.set(key, value);
    }
  });
  return new Response(response.body, { status: response.status, headers: outgoing });
}

export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
export const PATCH = proxy;
export const DELETE = proxy;
