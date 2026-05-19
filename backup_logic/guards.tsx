"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { getToken } from "@/lib/auth/tokenStore";
import { routes } from "@/lib/config/routes";
import { useSession } from "@/lib/auth/session";
import type { Role } from "@/lib/api/types";

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const token = getToken();
  const { loading, me } = useSession();

  useEffect(() => {
    if (!token) {
      router.replace(routes.login);
      return;
    }
    if (!loading && !me) {
      router.replace(routes.login);
    }
  }, [token, loading, me, router, pathname]);

  if (!token) return null;
  if (loading) return null;
  if (!me) return null;

  return <>{children}</>;
}

export function RoleGuard({ allow, children }: { allow: Role | "any"; children: React.ReactNode }) {
  const router = useRouter();
  const { loading, me } = useSession();

  useEffect(() => {
    if (!loading && me && allow !== "any" && me.role !== allow) {
      router.replace(me.role === "admin" ? routes.adminDashboard : routes.appDashboard);
    }
  }, [allow, loading, me, router]);

  if (loading) return null;
  if (!me) return null;
  if (allow !== "any" && me.role !== allow) return null;

  return <>{children}</>;
}
