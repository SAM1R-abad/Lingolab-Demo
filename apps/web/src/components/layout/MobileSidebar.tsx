"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { X, LayoutDashboard, ClipboardList, PenLine, TrendingUp, UserCog, ShieldCheck, Users } from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/hooks/useAuth";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard, exact: true },
  { href: "/dashboard/assessment", label: "Placement test", icon: ClipboardList, exact: false },
  { href: "/dashboard/writing", label: "Writing", icon: PenLine, exact: false },
  { href: "/dashboard/progress", label: "Progress", icon: TrendingUp, exact: false },
  { href: "/dashboard/profile", label: "Profile", icon: UserCog, exact: false },
];

export function MobileSidebar({ open, onClose }: { open: boolean; onClose: () => void }) {
  const pathname = usePathname();
  const { user } = useAuth();
  const items = [
    ...NAV_ITEMS,
    ...(user?.role === "admin"
      ? [
          { href: "/dashboard/admin/questions", label: "Admin · Questions", icon: ShieldCheck, exact: false },
          { href: "/dashboard/admin/users", label: "Admin · Users", icon: Users, exact: false },
        ]
      : []),
  ];

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-40 md:hidden">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} aria-hidden="true" />
      <div className="absolute inset-y-0 left-0 w-64 bg-surface p-4 shadow-md">
        <div className="mb-4 flex items-center justify-between">
          <span className="text-h4 font-semibold text-ku-dark-green">Menu</span>
          <button
            type="button"
            onClick={onClose}
            className="rounded-input p-2 text-text-secondary hover:bg-background"
            aria-label="Close navigation menu"
          >
            <X className="h-5 w-5" aria-hidden="true" />
          </button>
        </div>
        <nav className="flex flex-col gap-1">
          {items.map((item) => {
            const isActive = item.exact ? pathname === item.href : pathname.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={onClose}
                className={cn(
                  "flex items-center gap-3 rounded-input px-3 py-2 text-small font-medium",
                  isActive
                    ? "bg-ku-soft-green/50 text-ku-dark-green"
                    : "text-text-secondary hover:bg-background"
                )}
              >
                <item.icon className="h-5 w-5" aria-hidden="true" />
                {item.label}
              </Link>
            );
          })}
        </nav>
      </div>
    </div>
  );
}
