import { NextRequest, NextResponse } from "next/server"

function getBackendBaseUrl(): string {
  const raw = process.env.API_PROXY_TARGET || process.env.NEXT_PUBLIC_API_BASE_URL || ""
  const cleaned = raw.trim().replace(/\/+$/, "")
  // Accept either "https://host" or "https://host/api" in env config.
  return cleaned.replace(/\/api$/i, "")
}

async function proxyToBackend(request: NextRequest, path: string[]): Promise<NextResponse> {
  const base = getBackendBaseUrl()
  if (!base) {
    return NextResponse.json(
      {
        error:
          "Backend proxy target is not configured. Set API_PROXY_TARGET (preferred) or NEXT_PUBLIC_API_BASE_URL.",
      },
      { status: 500 },
    )
  }

  const targetUrl = `${base}/api/${path.join("/")}${request.nextUrl.search || ""}`

  // Copy incoming headers, but let fetch/runtime derive host/content-length.
  const headers = new Headers(request.headers)
  headers.delete("host")
  headers.delete("content-length")

  const method = request.method.toUpperCase()
  const hasBody = !["GET", "HEAD"].includes(method)
  const body = hasBody ? await request.arrayBuffer() : undefined

  const upstream = await fetch(targetUrl, {
    method,
    headers,
    body,
    redirect: "follow",
  })

  const responseHeaders = new Headers(upstream.headers)
  responseHeaders.delete("content-encoding")
  responseHeaders.delete("transfer-encoding")

  return new NextResponse(upstream.body, {
    status: upstream.status,
    headers: responseHeaders,
  })
}

export async function GET(request: NextRequest, context: { params: { path: string[] } }) {
  return proxyToBackend(request, context.params.path)
}

export async function POST(request: NextRequest, context: { params: { path: string[] } }) {
  return proxyToBackend(request, context.params.path)
}

export async function PUT(request: NextRequest, context: { params: { path: string[] } }) {
  return proxyToBackend(request, context.params.path)
}

export async function PATCH(request: NextRequest, context: { params: { path: string[] } }) {
  return proxyToBackend(request, context.params.path)
}

export async function DELETE(request: NextRequest, context: { params: { path: string[] } }) {
  return proxyToBackend(request, context.params.path)
}

export async function OPTIONS(request: NextRequest, context: { params: { path: string[] } }) {
  return proxyToBackend(request, context.params.path)
}
