"use client";

import DashboardLayout from "@/components/layout/DashboardLayout";
import { AuthGuard, RoleGuard } from "@/lib/auth/guards";

export function AppShell({
  children,
}: {
  title: string;
  subtitle: string;
  userLabel: string;
  nav: any[];
  children: React.ReactNode;
}) {
  return (
    <AuthGuard>
      <RoleGuard allow="any">
        <DashboardLayout>
          {children}
        </DashboardLayout>
      </RoleGuard>
    </AuthGuard>
  );
}
