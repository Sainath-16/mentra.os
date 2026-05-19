"use client";

import React from "react";
import PremiumSidebar from "./PremiumSidebar";
import PremiumTopbar from "./PremiumTopbar";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
    return (
        <div className="relative flex bg-[#FCFCFC] min-h-screen text-foreground selection:bg-black/10 selection:text-black font-sans overflow-hidden">

            {/* --- PREMIUM BACKGROUND ENGINE --- */}
            <div className="fixed inset-0 z-0 pointer-events-none flex items-center justify-center overflow-hidden">
                <div
                    className="absolute inset-0 opacity-[0.04] mix-blend-overlay"
                    style={{ backgroundImage: "url('https://grainy-gradients.vercel.app/noise.svg')" }}
                />

                {/* Ambient Glows */}
                <div className="absolute top-[-20%] left-[-10%] w-[60%] h-[60%] bg-black/[0.015] blur-[140px] rounded-full" />
                <div className="absolute bottom-[-20%] right-[-10%] w-[60%] h-[60%] bg-black/[0.015] blur-[140px] rounded-full" />
            </div>

            {/* Main Dashboard Layout Container */}
            <div className="relative z-10 flex w-full p-4 lg:p-6 gap-6 h-screen overflow-hidden">
                {/* Sidebar Desktop */}
                <PremiumSidebar />

                {/* Main Content Area */}
                <div className="flex-1 flex flex-col min-w-0 bg-white shadow-strong rounded-[2.5rem] border border-black/[0.08] overflow-hidden">
                    <PremiumTopbar />

                    <main className="flex-1 overflow-y-auto custom-scrollbar">
                        <div className="px-6 sm:px-10 py-10 w-full max-w-7xl mx-auto">
                            {children}
                        </div>
                    </main>
                </div>
            </div>
        </div>
    );
}
