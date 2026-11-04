// Generic route-handler template. Adapt names and imports to the target framework.

type RequestContext = {
  params?: Record<string, string | string[] | undefined>;
};

function requiredEnv(name: string): string {
  const value = process.env[name];
  if (!value) {
    throw new Error(`Missing ${name}`);
  }
  return value;
}

function json(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'content-type': 'application/json' }
  });
}

export async function GET(request: Request, _context: RequestContext): Promise<Response> {
  const baseUrl = requiredEnv('BACKEND_API_URL');
  const upstreamUrl = new URL('/replace-with-upstream-path', baseUrl);
  upstreamUrl.search = new URL(request.url).search;

  const upstream = await fetch(upstreamUrl, {
    headers: {
      accept: 'application/json'
    }
  });

  if (!upstream.ok) {
    if (upstream.status >= 500) {
      return json(502, { error: 'Upstream service failed' });
    }
    return json(upstream.status, { error: 'Request failed' });
  }

  const payload: unknown = await upstream.json();
  return json(200, payload);
}
