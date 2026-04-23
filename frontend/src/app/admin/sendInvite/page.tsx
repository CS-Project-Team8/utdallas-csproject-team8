"use client";
import React, { useMemo, useState } from "react";
import { Mail, Shield, User2, Send, ChevronDown } from "lucide-react";
import { getFirebaseAuth } from "@/lib/firebase";
import { useRouter } from "next/navigation";

type Role = "admin" | "user" | "viewer";

export default function SendInvitePage() {
  const [email, setEmail] = useState("");
  const router = useRouter();
  const [role, setRole] = useState<Role>("user");
  const [status, setStatus] = useState<"idle" | "sent" | "error">("idle");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const roleMeta = useMemo(() => {
    const map: Record<Role, { label: string; desc: string; icon: React.ReactNode }> = {
      admin: {
        label: "Admin",
        desc: "Can invite/manage users and studio settings.",
        icon: <Shield className="h-4 w-4" />,
      },
      user: {
        label: "User",
        desc: "Can analyze videos and view dashboards.",
        icon: <User2 className="h-4 w-4" />,
      },
      viewer: {
        label: "Viewer",
        desc: "Read-only access to analytics and reports.",
        icon: <User2 className="h-4 w-4" />,
      },
    };
    return map[role];
  }, [role]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setStatus("idle");
    setMessage("");

    try {
      const auth = getFirebaseAuth();

      if (!auth) {
        throw new Error("Authentication is not configured.");
      }

      const currentUser = auth.currentUser;
      if (!currentUser) {
        throw new Error("You must be logged in.");
      }

      const token = await currentUser.getIdToken();

      const baseUrl = (process.env.NEXT_PUBLIC_BACKEND_URL ?? "").replace(/\/+$/, "");

      const res = await fetch(`${baseUrl}/invites`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ email, role }),
      });

      const data = await res.json();

      if (!res.ok || !data.ok) {
        throw new Error(data.detail || "Failed to send invite");
      }

      setStatus("sent");
      setMessage("Invite sent successfully.");
      setEmail("");
      setRole("user");
    } catch (err: any) {
      console.error(err);
      setStatus("error");
      setMessage(err.message || "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className=" min-h-screen bg-black relative overflow-hidden flex items-center justify-center p-6">
      
      <div className="absolute w-[700px] h-[700px] bg-red-600/20 blur-[180px] rounded-full -top-56 -left-56" />
      <div className="absolute w-[520px] h-[520px] bg-red-500/10 blur-[160px] rounded-full bottom-[-220px] right-[-220px]" />
      <div className="absolute w-[420px] h-[420px] bg-red-700/10 blur-[160px] rounded-full top-[35%] right-[-200px]" />
      <div className="absolute top-6 right-6 z-20">
        <button
          onClick={() => router.push("./userList")}
          className="cursor-pointer rounded-xl border border-white/15 bg-white/10 backdrop-blur-md text-white px-5 py-2 text-sm font-medium hover:bg-white/20 transition"
        >
          User List
        </button>
      </div>
      <div className="relative z-10 w-full max-w-lg rounded-3xl p-8 bg-gradient-to-b from-white/14 to-white/6 backdrop-blur-3xl border border-white/18 shadow-[0_20px_70px_rgba(0,0,0,0.65)] overflow-hidden">
        
        <div className="pointer-events-none absolute -top-24 left-0 right-0 h-40 bg-gradient-to-b from-white/30 to-transparent blur-2xl" />
          
        <div className="flex items-start justify-between gap-4">
          
          <div>
            <h1 className="text-2xl font-semibold text-white tracking-tight">
              Invite a teammate
            </h1>
            <p className="text-sm text-white/70 mt-1">
              Send an invite link and assign a role.
            </p>
          </div>

          <div className="h-10 w-10 rounded-2xl border border-white/15 bg-white/10 grid place-items-center">
            <Send className="h-4 w-4 text-white/80" />
          </div>
        </div>

        <form onSubmit={onSubmit} className="mt-8 space-y-5">
          <div className="space-y-2">
            <label className="text-sm text-white/80">User email</label>
            <div className="flex items-center gap-2 rounded-2xl border border-white/15 bg-white/8 px-4 py-3 focus-within:border-red-500/50">
              <Mail className="h-4 w-4 text-white/60" />
              <input
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                type="email"
                required
                placeholder="name@company.com"
                className="w-full bg-transparent outline-none text-white placeholder:text-white/35 text-sm"
              />
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-sm text-white/80">Role</label>

            <div className="relative">
              <select
                value={role}
                onChange={(e) => setRole(e.target.value as Role)}
                className="w-full appearance-none rounded-2xl border border-white/15 bg-white/8 px-4 py-3 pr-10 text-white text-sm outline-none focus:border-red-500/50"
              >
                <option value="user" className="text-black">User</option>
                <option value="admin" className="text-black">Admin</option>
                <option value="viewer" className="text-black">Viewer</option>
              </select>

              <div className="pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 text-white/55">
                <ChevronDown className="h-4 w-4" />
              </div>
            </div>

            <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
              <div className="flex items-center gap-2 text-white/90">
                <span className="grid place-items-center h-7 w-7 rounded-xl bg-white/8 border border-white/10">
                  {roleMeta.icon}
                </span>
                <p className="text-sm font-medium">{roleMeta.label}</p>
              </div>
              <p className="text-xs text-white/65 mt-2">{roleMeta.desc}</p>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="cursor-pointer w-full rounded-2xl bg-red-600 text-white py-3 text-sm font-semibold hover:bg-red-500 active:scale-[0.99] transition shadow-[0_10px_30px_rgba(239,68,68,0.25)] disabled:opacity-60"
          >
            {loading ? "Sending..." : "Send invite"}
          </button>

          {message && (
            <div
              className={`rounded-2xl border px-4 py-3 text-sm ${
                status === "sent"
                  ? "border-green-500/30 bg-green-500/10 text-green-300"
                  : "border-red-500/30 bg-red-500/10 text-red-300"
              }`}
            >
              {message}
            </div>
          )}

          <p className="text-xs text-white/50">
            Security note: real flow uses one-time expiring tokens and logs who invited whom.
          </p>
        </form>
      </div>
    </div>
  );
}