"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { clearToken } from "@/lib/auth/tokenStore";
import { cn } from "@/lib/utils/cn";

export type NavItem = { href: string; label: string };

export function Sidebar({ title, subtitle, userLabel, items }: { title: string; subtitle: string; userLabel: string; items: NavItem[] }) {
  const pathname = usePathname();
  const router = useRouter();

  return (
    <aside className="hidden h-dvh w-72 flex-col border-r bg-white px-4 py-6 md:flex">
      <div className="px-2">
        <div className="text-sm font-extrabold tracking-tight text-slate-900">{title}</div>
        <div className="mt-1 text-xs text-slate-600">{subtitle}</div>
      </div>

      <div className="mt-6 rounded-2xl border bg-slate-50 px-4 py-3">
        <div className="text-xs text-slate-600">Signed in as</div>
        <div className="text-sm font-semibold text-slate-900">{userLabel}</div>
      </div>

      <nav className="mt-6 flex flex-1 flex-col gap-1">
        {items.map((i) => {
          const active = pathname === i.href;
          return (
            <Link
              key={i.href}
              href={i.href}
              className={cn(
                "rounded-2xl px-4 py-3 text-sm font-semibold transition",
                active ? "bg-slate-900 text-white" : "text-slate-700 hover:bg-slate-50"
              )}
            >
              {i.label}
            </Link>
          );
        })}
      </nav>

      <button
        onClick={() => {
          clearToken();
          router.replace("/login");
        }}
        className="mt-4 rounded-2xl border px-4 py-3 text-sm font-semibold text-slate-700 hover:bg-slate-50"
      >
        Logout
      </button>
    </aside>
  );
}
