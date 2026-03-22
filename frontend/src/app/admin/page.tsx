"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { signInWithEmailAndPassword } from "firebase/auth";
import { auth } from "@/lib/firebase";

export default function AdminLoginPage() {
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const cred = await signInWithEmailAndPassword(auth, email, password);
      const token = await cred.user.getIdToken();

      const res = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/auth/admin-login-check`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      const data = await res.json();

      if (!res.ok || !data.ok) {
        if (res.status === 404) {
          setError("User not found in database.");
        } else if (res.status === 403) {
          setError("You are not an admin.");
        } else if (res.status === 401) {
          setError("Unauthorized. Please log in again.");
        } else {
          setError(data.detail || "Admin login failed.");
        }
        return;
      }

      router.push("./admin/sendInvite");
    } catch (err: any) {
      console.error(err);
      switch (err.code) {
        case "auth/invalid-credential":
        case "auth/wrong-password":
        case "auth/user-not-found":
        case "auth/invalid-email":
          setError("Invalid email or password.");
          break;
        case "auth/too-many-requests":
          setError("Too many failed attempts. Please try again later.");
          break;
        case "auth/network-request-failed":
          setError("Network error. Check your internet connection.");
          break;
        default:
          setError(err.message || "Login failed.");
        }
      } finally {
        setLoading(false);
      }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-black relative overflow-hidden">
      <div className="absolute w-[600px] h-[600px] bg-red-600/20 blur-[160px] rounded-full -top-40 -left-40" />
      <div className="absolute w-[500px] h-[500px] bg-red-500/10 blur-[140px] rounded-full bottom-0 right-0" />

      <div className="relative z-10 w-full max-w-md p-10 rounded-2xl bg-white/5 backdrop-blur-xl border border-white/10 shadow-2xl">
        <h1 className="text-3xl font-semibold text-white text-center mb-8 tracking-wide">
          Admin Login
        </h1>

        <form className="space-y-5" onSubmit={handleLogin}>
          <div>
            <label className="block text-sm text-gray-300 mb-2">Email</label>
            <input
              type="email"
              placeholder="admin@studio.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-3 rounded-lg bg-black/60 border border-white/10 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-red-600 transition"
              required
            />
          </div>

          <div>
            <label className="block text-sm text-gray-300 mb-2">Password</label>
            <input
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-3 rounded-lg bg-black/60 border border-white/10 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-red-600 transition"
              required
            />
          </div>

          <div className="text-right">
            <Link
              href="/admin/forgot-password"
              className="text-sm text-red-500 hover:text-red-400 transition"
            >
              Forgot password?
            </Link>
          </div>

          {error && (
            <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="cursor-pointer w-full py-3 mt-2 rounded-lg bg-red-600 hover:bg-red-700 text-white font-medium transition shadow-lg shadow-red-600/30 disabled:opacity-60"
          >
            {loading ? "Signing In..." : "Sign In"}
          </button>
        </form>
      </div>
    </div>
  );
}