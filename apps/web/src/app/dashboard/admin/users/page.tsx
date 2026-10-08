"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Users as UsersIcon, Trash2 } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { useToast } from "@/hooks/useToast";
import { Card, CardHeader } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { FullPageSpinner, ErrorState, Spinner } from "@/components/ui/feedback";
import { EmptyState } from "@/components/ui/EmptyState";
import { ConfirmDialog, useConfirmDialog } from "@/components/ui/ConfirmDialog";
import { api, ApiError } from "@/services/api";
import type { AdminUser, Role } from "@/services/types";

const ROLE_OPTIONS: Role[] = ["student", "teacher", "admin"];

const ROLE_BADGE_TONE: Record<Role, "green" | "blue" | "cream"> = {
  admin: "green",
  teacher: "blue",
  student: "cream",
};

export default function AdminUsersPage() {
  const { user, isLoading: authLoading } = useAuth();
  const router = useRouter();
  const toast = useToast();

  const [users, setUsers] = useState<AdminUser[] | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  // Track per-row in-flight PATCH so only that row's controls disable.
  const [savingId, setSavingId] = useState<number | null>(null);

  const deleteDialog = useConfirmDialog();
  const [pendingDelete, setPendingDelete] = useState<AdminUser | null>(null);

  useEffect(() => {
    if (!authLoading && user && user.role !== "admin") {
      toast.error("This page requires an admin account.");
      router.replace("/dashboard");
    }
  }, [authLoading, user, router, toast]);

  const load = async () => {
    setIsLoading(true);
    setLoadError(null);
    try {
      const data = await api.adminUsers();
      setUsers(data);
    } catch (err) {
      setLoadError(err instanceof ApiError ? err.message : "Could not load users.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (user?.role === "admin") load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  const handleRoleChange = async (target: AdminUser, role: Role) => {
    if (role === target.role) return;
    setSavingId(target.id);
    try {
      const updated = await api.adminUpdateUser(target.id, { role });
      setUsers((prev) => prev && prev.map((u) => (u.id === target.id ? updated : u)));
      toast.success(`${target.username}'s role changed to ${role}.`);
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Could not update this user's role.");
    } finally {
      setSavingId(null);
    }
  };

  const handleToggleActive = async (target: AdminUser) => {
    setSavingId(target.id);
    try {
      const updated = await api.adminUpdateUser(target.id, { is_active: !target.is_active });
      setUsers((prev) => prev && prev.map((u) => (u.id === target.id ? updated : u)));
      toast.success(updated.is_active ? `${target.username} reactivated.` : `${target.username} deactivated.`);
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Could not update this user's status.");
    } finally {
      setSavingId(null);
    }
  };

  const confirmDelete = (target: AdminUser) => {
    setPendingDelete(target);
    deleteDialog.open();
  };

  const handleDelete = async () => {
    if (!pendingDelete) return;
    deleteDialog.setLoading(true);
    try {
      await api.adminDeleteUser(pendingDelete.id);
      toast.success(`${pendingDelete.username} deleted.`);
      deleteDialog.close();
      setPendingDelete(null);
      load();
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Could not delete this user.");
    } finally {
      deleteDialog.setLoading(false);
    }
  };

  if (authLoading || !user) return <FullPageSpinner label="Checking access..." />;
  if (user.role !== "admin") return null; // redirect already in flight

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-h2 text-text-primary">User management</h1>
        <p className="mt-1 text-body text-text-secondary">
          View every account, change roles, deactivate, or permanently delete a user.
        </p>
      </div>

      <Card>
        <CardHeader
          title="All users"
          description={users ? `${users.length} account${users.length === 1 ? "" : "s"}` : undefined}
        />

        {isLoading ? (
          <div className="flex justify-center py-10">
            <Spinner className="h-7 w-7" />
          </div>
        ) : loadError ? (
          <ErrorState message={loadError} onRetry={load} />
        ) : !users || users.length === 0 ? (
          <EmptyState icon={UsersIcon} title="No users yet" description="Accounts will show up here as people sign up." />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[720px] text-left text-small">
              <thead>
                <tr className="border-b border-border text-caption text-text-secondary">
                  <th className="py-2 pr-4 font-medium">User</th>
                  <th className="py-2 pr-4 font-medium">Role</th>
                  <th className="py-2 pr-4 font-medium">Status</th>
                  <th className="py-2 pr-4 font-medium">Joined</th>
                  <th className="py-2 pr-4 text-right font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => {
                  const isSelf = u.id === user.id;
                  const isSaving = savingId === u.id;
                  return (
                    <tr key={u.id} className="border-b border-border last:border-0">
                      <td className="py-3 pr-4">
                        <div className="flex flex-col">
                          <span className="font-medium text-text-primary">
                            {u.username}
                            {isSelf && <span className="ml-2 text-caption text-text-secondary">(you)</span>}
                          </span>
                          <span className="text-caption text-text-secondary">{u.email || "—"}</span>
                          {u.is_guest && (
                            <Badge tone="neutral" className="mt-1 w-fit">
                              Guest
                            </Badge>
                          )}
                        </div>
                      </td>
                      <td className="py-3 pr-4">
                        <select
                          value={u.role}
                          disabled={isSelf || isSaving}
                          onChange={(e) => handleRoleChange(u, e.target.value as Role)}
                          className="h-9 rounded-input border border-border bg-surface px-2 text-small text-text-primary disabled:opacity-50"
                          aria-label={`Change role for ${u.username}`}
                        >
                          {ROLE_OPTIONS.map((r) => (
                            <option key={r} value={r}>
                              {r}
                            </option>
                          ))}
                        </select>
                        <Badge tone={ROLE_BADGE_TONE[u.role]} className="ml-2 hidden capitalize sm:inline-flex">
                          {u.role}
                        </Badge>
                      </td>
                      <td className="py-3 pr-4">
                        <button
                          type="button"
                          disabled={isSelf || isSaving}
                          onClick={() => handleToggleActive(u)}
                          className="disabled:cursor-not-allowed disabled:opacity-50"
                          aria-label={`${u.is_active ? "Deactivate" : "Reactivate"} ${u.username}`}
                        >
                          <Badge tone={u.is_active ? "success" : "warning"}>
                            {u.is_active ? "Active" : "Deactivated"}
                          </Badge>
                        </button>
                      </td>
                      <td className="py-3 pr-4 text-text-secondary">
                        {new Date(u.date_joined).toLocaleDateString()}
                      </td>
                      <td className="py-3 pr-4">
                        <div className="flex justify-end">
                          <button
                            type="button"
                            disabled={isSelf}
                            onClick={() => confirmDelete(u)}
                            className="rounded-input p-2 text-text-secondary hover:bg-background hover:text-danger disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:bg-transparent disabled:hover:text-text-secondary"
                            aria-label={`Delete ${u.username}`}
                            title={isSelf ? "You can't delete your own account here." : "Delete user"}
                          >
                            <Trash2 className="h-4 w-4" aria-hidden="true" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      <ConfirmDialog
        open={deleteDialog.isOpen}
        title="Delete this user?"
        description={
          pendingDelete
            ? `"${pendingDelete.username}" will be permanently deleted, along with their session history.`
            : ""
        }
        confirmLabel="Delete user"
        isLoading={deleteDialog.isLoading}
        onConfirm={handleDelete}
        onCancel={deleteDialog.close}
      />
    </div>
  );
}
