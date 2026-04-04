"use client";

import { useEffect } from "react";
import { usePathname } from "next/navigation";
import { AdminSidebar } from "./AdminSidebar";
import { getToken } from "@/lib/auth";

interface AdminLayoutProps {
  children: React.ReactNode;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function AdminLayout({ children }: AdminLayoutProps) {
  const pathname = usePathname();

  // Auth + admin guard
  useEffect(() => {
    const token = getToken();
    if (!token) {
      window.location.href = "/landing";
      return;
    }
    // Verify admin status
    fetch(`${API_URL}/api/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (!data?.is_admin) {
          window.location.href = "/";
        }
      });
  }, []);

  return (
    <div className="flex h-screen bg-[#0a0a0f] overflow-hidden">
      <AdminSidebar currentPath={pathname ?? "/admin"} />
      <main className="flex-1 overflow-auto bg-[#12121a]">
        {children}
      </main>
    </div>
  );
}
