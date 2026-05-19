"use client";

import React, { useState } from "react";
import { Bell, Search, User, LogOut, Settings, Key } from "lucide-react";
import { cn } from "@/lib/utils";
import { motion, AnimatePresence } from "framer-motion";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useSession } from "@/lib/auth/session";
import { clearToken } from "@/lib/auth/tokenStore";

export default function PremiumTopbar() {
    const { me } = useSession();
    const router = useRouter();
    const [isNotificationOpen, setIsNotificationOpen] = useState(false);
    const [isProfileOpen, setIsProfileOpen] = useState(false);

    const userName = me?.username || "Operator";
    const initials = userName.charAt(0).toUpperCase();

    const handleLogout = () => {
        clearToken();
        router.replace("/login");
    };

    return (
        <header className="sticky top-0 z-40 flex h-20 flex-shrink-0 items-center justify-between border-b border-black/[0.05] bg-white/70 backdrop-blur-2xl px-6 lg:px-10">
            {/* Search */}
            <div className="flex flex-1 max-w-lg">
                <form className="relative flex w-full" action="#" method="GET" onSubmit={(e) => e.preventDefault()}>
                    <label htmlFor="search-field" className="sr-only">Search insights...</label>
                    <Search
                        className="pointer-events-none absolute inset-y-0 left-4 h-full w-4 text-black/30"
                        aria-hidden="true"
                    />
                    <input
                        id="search-field"
                        className="block h-11 w-full rounded-2xl border border-black/[0.08] bg-white/50 px-10 py-2 text-sm text-black placeholder:text-black/30 placeholder:uppercase placeholder:text-[10px] placeholder:tracking-widest placeholder:font-bold focus:border-black/[0.15] focus:bg-white focus:ring-0 focus:outline-none transition-all shadow-sm"
                        placeholder="Search predictions or activity logs..."
                        type="search"
                        name="search"
                    />
                </form>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-x-4 lg:gap-x-6 ml-4">

                {/* Notifications */}
                <div className="relative">
                    <button
                        onClick={() => {
                            setIsNotificationOpen(!isNotificationOpen);
                            if (isProfileOpen) setIsProfileOpen(false);
                        }}
                        className={cn(
                            "relative flex items-center justify-center w-11 h-11 rounded-full border border-black/[0.08] transition-all group shadow-sm",
                            isNotificationOpen ? "bg-black" : "bg-white hover:bg-black/5"
                        )}
                    >
                        <Bell
                            className={cn(
                                "h-5 w-5 transition-colors",
                                isNotificationOpen ? "text-white" : "text-black/60 group-hover:text-black"
                            )}
                        />
                    </button>

                    <AnimatePresence>
                        {isNotificationOpen && (
                            <motion.div
                                initial={{ opacity: 0, y: 10, scale: 0.95 }}
                                animate={{ opacity: 1, y: 0, scale: 1 }}
                                exit={{ opacity: 0, y: 10, scale: 0.95 }}
                                transition={{ duration: 0.2 }}
                                className="absolute right-0 mt-3 w-80 bg-white rounded-3xl shadow-strong border border-black/[0.08] overflow-hidden origin-top-right z-50 p-6 text-center"
                            >
                                <p className="text-xs font-bold uppercase tracking-widest text-black/40">No new notifications</p>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>

                <div className="h-6 w-px bg-black/[0.08]" aria-hidden="true" />

                {/* Profile Dropdown */}
                <div className="relative">
                    <button
                        onClick={() => {
                            setIsProfileOpen(!isProfileOpen);
                            if (isNotificationOpen) setIsNotificationOpen(false);
                        }}
                        className="flex items-center gap-x-2 rounded-full p-1 hover:bg-black/5 transition-all group"
                    >
                        <div className={cn(
                            "h-10 w-10 flex border-[1.5px] items-center justify-center rounded-full transition-all shadow-sm overflow-hidden",
                            isProfileOpen ? "bg-black border-black" : "bg-white border-black/[0.08] group-hover:bg-black group-hover:border-black"
                        )}>
                            {me?.avatar_url ? (
                                <img src={me.avatar_url} alt={userName} className="w-full h-full object-cover" />
                            ) : (
                                <User className={cn(
                                    "h-5 w-5 transition-colors",
                                    isProfileOpen ? "text-white" : "text-black/60 group-hover:text-white"
                                )} />
                            )}
                        </div>
                        <span className="text-[10px] font-bold uppercase tracking-widest text-black hidden sm:block">{initials}</span>
                    </button>

                    <AnimatePresence>
                        {isProfileOpen && (
                            <motion.div
                                initial={{ opacity: 0, y: 10, scale: 0.95 }}
                                animate={{ opacity: 1, y: 0, scale: 1 }}
                                exit={{ opacity: 0, y: 10, scale: 0.95 }}
                                transition={{ duration: 0.2 }}
                                className="absolute right-0 mt-3 w-64 bg-white rounded-3xl shadow-strong border border-black/[0.08] overflow-hidden origin-top-right z-50 p-2"
                            >
                                <div className="px-4 py-4 border-b border-black/[0.05] mb-2 flex items-center gap-3">
                                    <div className="w-10 h-10 rounded-full bg-black/[0.03] border border-black/[0.08] flex items-center justify-center shrink-0">
                                        <span className="text-sm font-black text-black">{initials}</span>
                                    </div>
                                    <div>
                                        <p className="text-xs font-black uppercase tracking-tighter text-black">{userName}</p>
                                        <p className="text-[10px] font-bold tracking-widest uppercase text-black/40 mt-0.5">{me?.role || "user"}</p>
                                    </div>
                                </div>

                                <div className="space-y-1">
                                    <Link
                                        href="/app/account"
                                        onClick={() => setIsProfileOpen(false)}
                                        className="flex items-center gap-3 w-full px-4 py-3 rounded-2xl hover:bg-black/[0.04] text-[10px] font-bold uppercase tracking-widest text-black/60 hover:text-black transition-all group"
                                    >
                                        <Settings className="w-4 h-4 text-black/30 group-hover:text-black" />
                                        Account Settings
                                    </Link>
                                    <Link
                                        href="/forgot-password"
                                        onClick={() => setIsProfileOpen(false)}
                                        className="flex items-center gap-3 w-full px-4 py-3 rounded-2xl hover:bg-black/[0.04] text-[10px] font-bold uppercase tracking-widest text-black/60 hover:text-black transition-all group"
                                    >
                                        <Key className="w-4 h-4 text-black/30 group-hover:text-black" />
                                        Reset Password
                                    </Link>
                                    <button
                                        onClick={handleLogout}
                                        className="flex items-center gap-3 w-full px-4 py-3 rounded-2xl hover:bg-red-500/10 text-[10px] font-bold uppercase tracking-widest text-red-500/60 hover:text-red-500 transition-all group mt-2 border-t border-black/[0.02] pt-3"
                                    >
                                        <LogOut className="w-4 h-4 text-red-500/30 group-hover:text-red-500" />
                                        Sign Out
                                    </button>
                                </div>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>
            </div>
        </header>
    );
}
