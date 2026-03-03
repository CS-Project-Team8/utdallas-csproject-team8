"use client";

import React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

export default function AdminLoginPage() {
    const router = useRouter();
    return (
        <div className="min-h-screen flex items-center justify-center bg-black relative overflow-hidden">

            {/* Subtle Red Glow Background */}
            <div className="absolute w-[600px] h-[600px] bg-red-600/20 blur-[160px] rounded-full -top-40 -left-40" />
            <div className="absolute w-[500px] h-[500px] bg-red-500/10 blur-[140px] rounded-full bottom-0 right-0" />

            {/* Liquid Glass Card */}
            <div className="relative z-10 w-full max-w-md p-10 rounded-2xl 
                            bg-white/5 
                            backdrop-blur-xl 
                            border border-white/10 
                            shadow-2xl">

                {/* Title */}
                <h1 className="text-3xl font-semibold text-white text-center mb-8 tracking-wide">
                Admin Login
                </h1>

                {/* Form */}
                <form className="space-y-5">

                    {/* Email */}
                    <div>
                        <label className="block text-sm text-gray-300 mb-2">
                        Email
                        </label>
                        <input
                        type="email"
                        placeholder="admin@studio.com"
                        className="w-full px-4 py-3 rounded-lg 
                                    bg-black/60 
                                    border border-white/10 
                                    text-white 
                                    placeholder-gray-500
                                    focus:outline-none 
                                    focus:ring-2 
                                    focus:ring-red-600 
                                    transition"
                        />
                    </div>

                    {/* Password */}
                    <div>
                        <label className="block text-sm text-gray-300 mb-2">
                        Password
                        </label>
                        <input
                        type="password"
                        placeholder="••••••••"
                        className="w-full px-4 py-3 rounded-lg 
                                    bg-black/60 
                                    border border-white/10 
                                    text-white 
                                    placeholder-gray-500
                                    focus:outline-none 
                                    focus:ring-2 
                                    focus:ring-red-600 
                                    transition"
                        />
                    </div>

                    {/* Forgot Password */}
                    <div className="text-right">
                        <Link
                        href="/admin/forgot-password"
                        className="text-sm text-red-500 hover:text-red-400 transition"
                        >
                        Forgot password?
                        </Link>
                    </div>

                    {/* Submit Button */}
                    <button
                        type="submit"
                        onClick={() => router.push("/sendInvite")}
                        className="cursor-pointer w-full py-3 mt-2 rounded-lg 
                                bg-red-600 
                                hover:bg-red-700 
                                text-white 
                                font-medium 
                                transition 
                                shadow-lg 
                                shadow-red-600/30"
                    >
                        Sign In
                    </button>
                </form>
            </div>
        </div>
    );
}