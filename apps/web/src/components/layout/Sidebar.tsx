"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { BookOpenCheck, LayoutDashboard, ClipboardList, PenLine, TrendingUp, UserCog, ShieldCheck, Users } from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/hooks/useAuth";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard, exact: true },
  { href: "/dashboard/assessment", label: "Placement test", icon: ClipboardList, exact: false },
  { href: "/dashboard/writing", label: "Writing", icon: PenLine, exact: false },
  { href: "/dashboard/progress", label: "Progress", icon: TrendingUp, exact: false },
  { href: "/dashboard/profile", label: "Profile", icon: UserCog, exact: false },
];

export function Sidebar() {
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

  return (
    <aside className="hidden w-sidebar shrink-0 flex-col border-r border-border bg-surface md:flex">
      <div className="flex h-header items-center gap-2 border-b border-border px-6">
        <BookOpenCheck className="h-6 w-6 text-ku-green" aria-hidden="true" />
        <span className="text-h4 font-semibold text-ku-dark-green">LingoLab</span>
      </div>
      <nav className="flex flex-col gap-1 p-4">
        {items.map((item) => {
          const isActive = item.exact ? pathname === item.href : pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-input px-3 py-2 text-small font-medium transition-colors",
                isActive
                  ? "bg-ku-soft-green/50 text-ku-dark-green"
                  : "text-text-secondary hover:bg-background hover:text-text-primary"
              )}
              aria-current={isActive ? "page" : undefined}
            >
              <item.icon className="h-5 w-5" aria-hidden="true" />
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
