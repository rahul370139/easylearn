import { NextRequest, NextResponse } from "next/server"

function backendBase(): string {
  const raw = (process.env.API_PROXY_TARGET || process.env.NEXT_PUBLIC_API_BASE_URL || "").trim()
  return raw.replace(/\/+$/, "").replace(/\/api$/i, "")
}

export async function POST(request: NextRequest) {
  const base = backendBase()
  if (!base) {
    return NextResponse.json(
      { error: "Backend URL missing. Set API_PROXY_TARGET or NEXT_PUBLIC_API_BASE_URL." },
      { status: 500 },
    )
  }

  const target = `${base}/api/career/resume/parse${request.nextUrl.search || ""}`
  const headers = new Headers(request.headers)
  headers.delete("host")
  headers.delete("content-length")

  const upstream = await fetch(target, {
    method: "POST",
    headers,
    body: await request.arrayBuffer(),
    redirect: "follow",
  })

  const outHeaders = new Headers(upstream.headers)
  outHeaders.delete("content-encoding")
  outHeaders.delete("transfer-encoding")

  return new NextResponse(upstream.body, {
    status: upstream.status,
    headers: outHeaders,
  })
}
