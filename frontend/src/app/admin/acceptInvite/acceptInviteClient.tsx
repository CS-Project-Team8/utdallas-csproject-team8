"use client";

import { useSearchParams, useRouter } from "next/navigation";
import React, { useEffect, useState } from "react";

export default function AcceptInviteClient() {
  const searchParams = useSearchParams();
  const router = useRouter();

  const token = searchParams.get("token") || "";
  const email = searchParams.get("email") || "";

  const [displayName, setDisplayName] = useState("");
  const [password, setPassword] = useState("");
  const [valid, setValid] = useState<boolean | null>(null);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    async function validateInvite() {
      try {
        const res = await fetch(
          `${process.env.NEXT_PUBLIC_BACKEND_URL}/invites/validate?token=${encodeURIComponent(token)}&email=${encodeURIComponent(email)}`
        );

        const data = await res.json();

        if (!res.ok || !data.ok) {
          setValid(false);
          setMessage(data.detail || "Invalid invite");
          return;
        }

        setValid(true);
      } catch {
        setValid(false);
        setMessage("Failed to validate invite");
      }
    }

    if (!token || !email) {
      setValid(false);
      setMessage("Missing token or email");
      return;
    }

    validateInvite();
  }, [token, email]);

  async function handleAccept(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setMessage("");

    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_BACKEND_URL}/invites/accept`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            token,
            email,
            password,
            display_name: displayName,
          }),
        }
      );

      const data = await res.json();

      if (!res.ok || !data.ok) {
        throw new Error(data.detail || "Failed to accept invite");
      }

      setMessage("Account created successfully. You can log in now.");
      setTimeout(() => {
        router.push("/admin");
      }, 1500);
    } catch (err: any) {
      setMessage(err.message || "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  if (valid === null) {
    return (
      <div className="min-h-screen bg-black text-white grid place-items-center">
        Checking invite...
      </div>
    );
  }

  if (!valid) {
    return (
      <div className="min-h-screen bg-black text-red-300 grid place-items-center">
        {message}
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black text-white grid place-items-center p-6">
      <form
        onSubmit={handleAccept}
        className="w-full max-w-md space-y-4 rounded-2xl border border-white/10 bg-white/5 p-8"
      >
        <h1 className="text-2xl font-semibold">Accept Invite</h1>
        <p className="text-sm text-white/70">{email}</p>

        <input
          type="text"
          placeholder="Full name"
          value={displayName}
          onChange={(e) => setDisplayName(e.target.value)}
          className="w-full rounded-lg border border-white/10 bg-black/50 px-4 py-3"
          required
        />

        <input
          type="password"
          placeholder="Create password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full rounded-lg border border-white/10 bg-black/50 px-4 py-3"
          required
        />

        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-lg bg-red-600 py-3 font-medium disabled:opacity-60"
        >
          {loading ? "Creating account..." : "Accept Invite"}
        </button>

        {message && <div className="text-sm text-white/80">{message}</div>}
      </form>
    </div>
  );
}