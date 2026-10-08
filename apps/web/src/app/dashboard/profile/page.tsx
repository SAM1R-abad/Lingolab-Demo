"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { UserCircle2, Trash2 } from "lucide-react";
import { Card, CardHeader } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { ConfirmDialog, useConfirmDialog } from "@/components/ui/ConfirmDialog";
import { useAuth } from "@/hooks/useAuth";
import { useToast } from "@/hooks/useToast";
import { ApiError } from "@/services/api";

const profileSchema = z.object({
  first_name: z.string().max(150, "Too long").optional().or(z.literal("")),
  last_name: z.string().max(150, "Too long").optional().or(z.literal("")),
  email: z.string().email("Enter a valid email address").optional().or(z.literal("")),
});

type ProfileFormValues = z.infer<typeof profileSchema>;

export default function ProfilePage() {
  const { user, updateProfile, deleteAccount } = useAuth();
  const toast = useToast();
  const deleteDialog = useConfirmDialog();

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting, isDirty },
  } = useForm<ProfileFormValues>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      first_name: user?.first_name ?? "",
      last_name: user?.last_name ?? "",
      email: user?.email ?? "",
    },
  });

  const onSubmit = async (values: ProfileFormValues) => {
    try {
      await updateProfile(values);
      toast.success("Profile updated.");
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Could not update your profile.");
    }
  };

  const handleDelete = async () => {
    deleteDialog.setLoading(true);
    try {
      await deleteAccount();
      toast.info("Your account has been deleted.");
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Could not delete your account.");
      deleteDialog.setLoading(false);
      deleteDialog.close();
    }
  };

  if (!user) return null;

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-6">
      <div>
        <h1 className="text-h2 text-text-primary">Profile</h1>
        <p className="mt-1 text-body text-text-secondary">Manage your account details.</p>
      </div>

      <Card>
        <div className="mb-6 flex items-center gap-4">
          <div className="flex h-14 w-14 items-center justify-center rounded-full bg-ku-soft-green/50">
            <UserCircle2 className="h-8 w-8 text-ku-dark-green" aria-hidden="true" />
          </div>
          <div>
            <p className="text-h4 text-text-primary">{user.username}</p>
            <div className="mt-1 flex items-center gap-2">
              <Badge tone="green" className="capitalize">
                {user.role}
              </Badge>
              {user.is_guest && <Badge tone="warning">Guest account</Badge>}
            </div>
          </div>
        </div>

        {user.is_guest ? (
          <p className="rounded-input bg-background px-3 py-3 text-small text-text-secondary">
            Guest accounts have no email or password, so there&apos;s nothing to edit here. Create a
            full account from the login screen to keep your progress long-term.
          </p>
        ) : (
          <form onSubmit={handleSubmit(onSubmit)} noValidate className="flex flex-col gap-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <Input label="First name" error={errors.first_name?.message} {...register("first_name")} />
              <Input label="Last name" error={errors.last_name?.message} {...register("last_name")} />
            </div>
            <Input label="Email" type="email" error={errors.email?.message} {...register("email")} />

            <Button
              type="submit"
              className="mt-2 w-full sm:w-auto"
              isLoading={isSubmitting}
              disabled={!isDirty}
            >
              Save changes
            </Button>
          </form>
        )}
      </Card>

      <Card className="border-danger/30">
        <CardHeader
          title="Danger zone"
          description="Permanently delete your account and all of your placement-test history. This cannot be undone."
        />
        <Button variant="danger" onClick={deleteDialog.open}>
          <Trash2 className="h-4 w-4" aria-hidden="true" />
          Delete my account
        </Button>
      </Card>

      <ConfirmDialog
        open={deleteDialog.isOpen}
        title="Delete your account?"
        description="This permanently removes your account and all placement-test history. This action cannot be undone."
        confirmLabel="Delete account"
        isLoading={deleteDialog.isLoading}
        onConfirm={handleDelete}
        onCancel={deleteDialog.close}
      />
    </div>
  );
}
