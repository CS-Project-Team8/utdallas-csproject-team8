"use client";

import React, { useMemo, useState } from "react";
import { Mail, Shield, User2, Send, ChevronDown } from "lucide-react";

type Role = "admin" | "user" | "viewer";

export default function SendInvitePage() {
    const [email, setEmail] = useState("");
    const [role, setRole] = useState<Role>("user");
    const [status, setStatus] = useState<"idle" | "sent">("idle");

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

    function onSubmit(e: React.FormEvent) {
        e.preventDefault();

        // later: call backend POST /invites with { email, role }
        console.log("Send invite:", { email, role });

        setStatus("sent");
        setTimeout(() => setStatus("idle"), 2500);
        setEmail("");
        setRole("user");
    }

    return (
        <div className="min-h-screen bg-black relative overflow-hidden flex items-center justify-center p-6">
            {/* Red glow blobs */}
            <div className="absolute w-[700px] h-[700px] bg-red-600/20 blur-[180px] rounded-full -top-56 -left-56" />
            <div className="absolute w-[520px] h-[520px] bg-red-500/10 blur-[160px] rounded-full bottom-[-220px] right-[-220px]" />
            <div className="absolute w-[420px] h-[420px] bg-red-700/10 blur-[160px] rounded-full top-[35%] right-[-200px]" />

            {/* Liquid glass card */}
            <div
                className="relative z-10 w-full max-w-lg rounded-3xl p-8
                        bg-gradient-to-b from-white/14 to-white/6
                        backdrop-blur-3xl border border-white/18
                        shadow-[0_20px_70px_rgba(0,0,0,0.65)]
                        overflow-hidden"
            >
                {/* Top highlight */}
                <div className="pointer-events-none absolute -top-24 left-0 right-0 h-40 bg-gradient-to-b from-white/30 to-transparent blur-2xl" />

                {/* Header */}
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

                {/* Form */}
                <form onSubmit={onSubmit} className="mt-8 space-y-5">
                    {/* Email */}
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

                    {/* Role */}
                    <div className="space-y-2">
                        <label className="text-sm text-white/80">Role</label>

                        <div className="relative">
                            <select
                                value={role}
                                onChange={(e) => setRole(e.target.value as Role)}
                                className="w-full appearance-none rounded-2xl border border-white/15 bg-white/8 px-4 py-3 pr-10
                                        text-white text-sm outline-none focus:border-red-500/50"
                            >
                                <option value="user" className="text-black">
                                User
                                </option>
                                <option value="admin" className="text-black">
                                Admin
                                </option>
                                <option value="viewer" className="text-black">
                                Viewer
                                </option>
                            </select>

                            <div className="pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 text-white/55">
                                <ChevronDown className="h-4 w-4" />
                            </div>
                        </div>

                        {/* Role hint */}
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

                    {/* Submit */}
                    <button
                        type="submit"
                        className="cursor-pointer w-full rounded-2xl bg-red-600 text-white py-3 text-sm font-semibold
                                hover:bg-red-500 active:scale-[0.99] transition
                                shadow-[0_10px_30px_rgba(239,68,68,0.25)]"
                    >
                        Send invite
                    </button>

                    {/* Success toast-ish */}
                    <div
                        className={`transition-all duration-300 ${
                        status === "sent" ? "opacity-100 translate-y-0" : "opacity-0 translate-y-1"
                        }`}
                    >
                        <div className="rounded-2xl border border-white/12 bg-white/6 px-4 py-3 text-sm text-white/80">
                        ✅ Invite queued (mock). You’ll hook this to your backend next.
                        </div>
                    </div>

                    {/* Footer note */}
                    <p className="text-xs text-white/50">
                        Security note: real flow uses one-time expiring tokens and logs who invited whom.
                    </p>
                </form>
            </div>
        </div>
    );
}