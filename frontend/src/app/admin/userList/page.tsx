"use client";

import React, { useEffect, useMemo, useState } from "react";
import { Shield, User2, Eye, Users, Search } from "lucide-react";
import { useRouter } from "next/navigation";
import { getFirebaseAuth } from "@/lib/firebase";

type Role = "admin" | "user" | "viewer";

type UserItem = {
  id: string;
  name: string;
  email: string;
  role: Role;
  status: "active" | "pending";
};

function getRoleMeta(role: Role) {
  const map = {
    admin: {
      label: "Admin",
      icon: <Shield className="h-4 w-4" />,
      badge: "border-red-500/30 bg-red-500/10 text-red-300",
    },
    user: {
      label: "User",
      icon: <User2 className="h-4 w-4" />,
      badge: "border-white/15 bg-white/8 text-white/85",
    },
    viewer: {
      label: "Viewer",
      icon: <Eye className="h-4 w-4" />,
      badge: "border-white/10 bg-white/5 text-white/70",
    },
  };

  return map[role];
}

export default function UserListPage() {
  const router = useRouter();

  const [search, setSearch] = useState("");
  const [users, setUsers] = useState<UserItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function fetchUsers() {
      try {
        setLoading(true);
        setError("");

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

        const res = await fetch(`${baseUrl}/auth/studio-users`, {
          method: "GET",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        const data = await res.json();

        if (!res.ok || !data.ok) {
          throw new Error(data.detail || "Failed to fetch users.");
        }

        setUsers(data.users || []);
      } catch (err: any) {
        console.error(err);
        setError(err.message || "Something went wrong while fetching users.");
      } finally {
        setLoading(false);
      }
    }

    fetchUsers();
  }, []);

  const filteredUsers = useMemo(() => {
    const term = search.toLowerCase().trim();

    if (!term) return users;

    return users.filter(
      (user) =>
        user.name.toLowerCase().includes(term) ||
        user.email.toLowerCase().includes(term) ||
        user.role.toLowerCase().includes(term)
    );
  }, [search, users]);

  return (
    <div className="min-h-screen bg-black relative overflow-hidden flex items-center justify-center p-6">
      <div className="absolute w-[700px] h-[700px] bg-red-600/20 blur-[180px] rounded-full -top-56 -left-56" />
      <div className="absolute w-[520px] h-[520px] bg-red-500/10 blur-[160px] rounded-full bottom-[-220px] right-[-220px]" />
      <div className="absolute w-[420px] h-[420px] bg-red-700/10 blur-[160px] rounded-full top-[35%] right-[-200px]" />

      <div className="absolute top-6 right-6 z-20">
        <button
          onClick={() => router.push("/admin/sendInvite")}
          className="cursor-pointer rounded-xl border border-white/15 bg-white/10 backdrop-blur-md text-white px-5 py-2 text-sm font-medium hover:bg-white/20 transition"
        >
          Send Invite
        </button>
      </div>

      <div className="relative z-10 w-full max-w-5xl rounded-3xl p-8 bg-gradient-to-b from-white/14 to-white/6 backdrop-blur-3xl border border-white/18 shadow-[0_20px_70px_rgba(0,0,0,0.65)] overflow-hidden">
        <div className="pointer-events-none absolute -top-24 left-0 right-0 h-40 bg-gradient-to-b from-white/30 to-transparent blur-2xl" />

        <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-semibold text-white tracking-tight">
              User List
            </h1>
            <p className="text-sm text-white/70 mt-1">
              View all users and their assigned roles.
            </p>
          </div>

          <div className="h-10 w-10 rounded-2xl border border-white/15 bg-white/10 grid place-items-center">
            <Users className="h-4 w-4 text-white/80" />
          </div>
        </div>

        <div className="mt-8 flex flex-col md:flex-row gap-4 md:items-center md:justify-between">
          <div className="w-full md:max-w-sm">
            <div className="flex items-center gap-2 rounded-2xl border border-white/15 bg-white/8 px-4 py-3 focus-within:border-red-500/50">
              <Search className="h-4 w-4 text-white/60" />
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                type="text"
                placeholder="Search by name, email, or role"
                className="w-full bg-transparent outline-none text-white placeholder:text-white/35 text-sm"
              />
            </div>
          </div>

          <div className="flex gap-3 text-xs">
            <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-white/70">
              Total Users:{" "}
              <span className="text-white font-semibold">{users.length}</span>
            </div>
            <div className="rounded-2xl border border-red-500/20 bg-red-500/10 px-4 py-3 text-red-300">
              Admins:{" "}
              <span className="font-semibold">
                {users.filter((u) => u.role === "admin").length}
              </span>
            </div>
          </div>
        </div>

        {loading && (
          <div className="mt-8 text-sm text-white/60">Loading users...</div>
        )}

        {error && (
          <div className="mt-8 rounded-2xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
            {error}
          </div>
        )}

        {!loading && !error && (
          <div className="mt-8 rounded-3xl border border-white/10 bg-white/5 overflow-hidden">
            <div className="hidden md:grid grid-cols-12 gap-4 px-6 py-4 border-b border-white/10 text-xs uppercase tracking-wide text-white/45">
              <div className="col-span-4">User</div>
              <div className="col-span-4">Email</div>
              <div className="col-span-2">Role</div>
              <div className="col-span-1">Status</div>
            </div>

            <div className="divide-y divide-white/10">
              {filteredUsers.length > 0 ? (
                filteredUsers.map((user) => {
                  const roleMeta = getRoleMeta(user.role);

                  return (
                    <div
                      key={user.id}
                      className="grid grid-cols-1 md:grid-cols-12 gap-4 px-6 py-5 hover:bg-white/[0.03] transition"
                    >
                      <div className="md:col-span-4">
                        <p className="text-white font-medium">{user.name}</p>
                      </div>

                      <div className="md:col-span-4">
                        <p className="text-sm text-white/70 break-all">{user.email}</p>
                      </div>

                      <div className="md:col-span-2">
                        <div
                          className={`inline-flex items-center gap-2 rounded-xl border px-3 py-1.5 text-xs font-medium ${roleMeta.badge}`}
                        >
                          {roleMeta.icon}
                          <span>{roleMeta.label}</span>
                        </div>
                      </div>

                      <div className="md:col-span-1">
                        <span
                          className={`inline-flex rounded-full px-2.5 py-1 text-xs border ${
                            user.status === "active"
                              ? "border-green-500/25 bg-green-500/10 text-green-300"
                              : "border-yellow-500/25 bg-yellow-500/10 text-yellow-300"
                          }`}
                        >
                          {user.status}
                        </span>
                      </div>
                    </div>
                  );
                })
              ) : (
                <div className="px-6 py-10 text-center text-white/55 text-sm">
                  No users found.
                </div>
              )}
            </div>
          </div>
        )}

        <p className="text-xs text-white/50 mt-6">
          Showing users from the same studio as the logged-in admin.
        </p>
      </div>
    </div>
  );
}