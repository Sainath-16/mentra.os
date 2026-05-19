"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { Activity, Home, BarChart3, ShieldCheck, Brain, History, Settings } from "lucide-react";

type NavItem = {
    name: string;
    href: string;
    icon: any;
};

const navigation: NavItem[] = [
    { name: "Dashboard", href: "/app/dashboard", icon: Home },
    { name: "Predict Stress", href: "/app/predict", icon: Brain },
    { name: "History", href: "/app/history", icon: History },
    { name: "Account", href: "/app/account", icon: ShieldCheck },
];

export default function PremiumSidebar() {
    const pathname = usePathname();

    return (
        <div className="flex h-full w-[260px] flex-col rounded-[2.5rem] bg-white/80 backdrop-blur-3xl px-5 py-8 text-black border border-black/[0.08] shadow-strong z-20 hidden md:flex transition-all duration-300">
            {/* Logo */}
            <div className="flex items-center space-x-3 px-2 mb-10 group cursor-pointer">
                <div className="w-10 h-10 bg-black rounded-xl flex items-center justify-center shadow-strong group-hover:scale-105 transition-transform">
                    <Brain className="h-5 w-5 text-white" />
                </div>
                <span className="font-black text-xl italic tracking-tighter uppercase">MENTRA.AI</span>
            </div>

            {/* Navigation */}
            <nav className="flex-1 space-y-1.5 custom-scrollbar overflow-y-auto pr-2">
                {navigation.map((item) => {
                    const isActive = pathname.startsWith(item.href);
                    return (
                        <Link
                            key={item.href}
                            href={item.href}
                            className={cn(
                                "group flex items-center space-x-3 rounded-2xl px-4 py-3.5 text-[11px] uppercase tracking-widest font-bold transition-all duration-300 hover:bg-black/5 hover:translate-x-1",
                                isActive
                                    ? "bg-black text-white shadow-strong hover:bg-black hover:translate-x-0"
                                    : "text-black/50 hover:text-black"
                            )}
                        >
                            <item.icon
                                className={cn(
                                    "h-4 w-4 flex-shrink-0 transition-colors duration-300",
                                    isActive ? "text-white" : "text-black/40 group-hover:text-black"
                                )}
                                aria-hidden="true"
                            />
                            <span className="italic">{item.name}</span>
                        </Link>
                    );
                })}
            </nav>

            {/* Footer Status Widget */}
            <div className="mt-8 pt-6 border-t border-black/[0.05]">
                <div className="rounded-[1.5rem] border border-black/[0.08] bg-black/[0.02] p-4 shadow-sm backdrop-blur-sm">
                    <p className="font-bold text-[10px] uppercase tracking-widest text-black mb-1 flex items-center gap-2">
                        Status <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                    </p>
                    <p className="text-[10px] font-medium tracking-tight text-black/40">
                        AI Core Connected
                    </p>
                </div>
            </div>
        </div>
    );
}
