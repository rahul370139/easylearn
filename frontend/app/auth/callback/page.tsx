'use client'

import { Suspense, useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { supabase } from '@/lib/supabase'

export const dynamic = 'force-dynamic'

function CallbackInner() {
  const router = useRouter()
  const searchParams = useSearchParams()

  useEffect(() => {
    let isMounted = true
    const handleCallback = async () => {
      try {
        const code = searchParams.get('code')
        if (code) {
          // OAuth (PKCE) flow
          await supabase.auth.exchangeCodeForSession(code)
        } else {
          // Email magic-link flow (tokens in URL hash)
          await supabase.auth.getSessionFromUrl({ storeSession: true })
        }
      } catch (err) {
        console.error('Auth callback error:', err)
      } finally {
        if (isMounted) router.replace('/')
      }
    }
    void handleCallback()
    return () => {
      isMounted = false
    }
  }, [router, searchParams])

  return (
    <div className="min-h-[60vh] flex items-center justify-center">
      <div className="space-y-3 text-center">
        <div className="mx-auto h-10 w-10 rounded-full border-2 border-primary border-t-transparent animate-spin" />
        <p className="text-sm text-muted-foreground">Finishing sign-in…</p>
      </div>
    </div>
  )
}

export default function AuthCallback() {
  return (
    <Suspense
      fallback={
        <div className="min-h-[60vh] flex items-center justify-center">
          <div className="space-y-3 text-center">
            <div className="mx-auto h-10 w-10 rounded-full border-2 border-primary border-t-transparent animate-spin" />
            <p className="text-sm text-muted-foreground">Loading…</p>
          </div>
        </div>
      }
    >
      <CallbackInner />
    </Suspense>
  )
}
