'use client';
import { supabase } from '@/lib/supabase';
import { useState } from 'react';

export default function Login() {
  const [email, setEmail] = useState('');
  const [sent, setSent] = useState(false);

  const handleLogin = async () => {
    await supabase.auth.signInWithOtp({
      email,
      options: { emailRedirectTo: `${location.origin}/auth/callback` },
    });
    setSent(true);
  };

  return (
    <div className="mx-auto max-w-md space-y-4">
      <h2 className="text-xl font-semibold">Log in or sign up</h2>
      {sent ? (
        <p>Magic link sent! Check your inbox.</p>
      ) : (
        <>
          <input
            type="email"
            placeholder="you@example.com"
            className="w-full rounded border p-2"
            onChange={(e) => setEmail(e.target.value)}
          />
          <button className="btn-primary w-full" onClick={handleLogin}>
            Send magic link
          </button>
        </>
      )}
    </div>
  );
}
