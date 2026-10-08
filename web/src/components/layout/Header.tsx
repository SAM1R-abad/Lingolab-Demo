"use client";

import { useState } from "react";
import { LogOut, UserCircle2, Menu } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { Badge } from "@/components/ui/Badge";
import { MobileSidebar } from "@/components/layout/MobileSidebar";

export function Header() {
  const { user, logout } = useAuth();
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  return (
    <header className="flex h-header items-center justify-between border-b border-border bg-surface px-4 md:px-8">
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={() => setMobileNavOpen(true)}
          className="rounded-input p-2 text-text-secondary hover:bg-background md:hidden"
          aria-label="Open navigation menu"
        >
          <Menu className="h-5 w-5" aria-hidden="true" />
        </button>
        <h1 className="text-h4 text-text-primary md:hidden">LingoLab</h1>
      </div>

      <div className="flex items-center gap-4">
        {user?.is_guest && <Badge tone="warning">Guest session</Badge>}
        <div className="flex items-center gap-2 text-small text-text-primary">
          <UserCircle2 className="h-6 w-6 text-text-secondary" aria-hidden="true" />
          <span className="hidden sm:inline">{user?.username}</span>
        </div>
        <button
          type="button"
          onClick={logout}
          className="flex items-center gap-2 rounded-input px-3 py-2 text-small text-text-secondary hover:bg-background hover:text-danger"
        >
          <LogOut className="h-4 w-4" aria-hidden="true" />
          <span className="hidden sm:inline">Log out</span>
        </button>
      </div>

      <MobileSidebar open={mobileNavOpen} onClose={() => setMobileNavOpen(false)} />
    </header>
  );
}
