"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { UserRound } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Alert } from "@/components/ui/Alert";
import { useAuth } from "@/hooks/useAuth";
import { useToast } from "@/hooks/useToast";
import { ApiError } from "@/services/api";

export function OrDivider() {
  return (
    <div className="my-6 flex items-center gap-3" role="separator">
      <div className="h-px flex-1 bg-border" />
      <span className="text-caption text-text-secondary">or</span>
      <div className="h-px flex-1 bg-border" />
    </div>
  );
}

export function GuestContinueButton() {
  const { continueAsGuest } = useAuth();
  const toast = useToast();
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleClick = async () => {
    setError(null);
    setIsLoading(true);
    try {
      await continueAsGuest();
      toast.info("Continuing as guest — sign up anytime to save your progress.");
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not start a guest session.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col gap-3">
      <Button
        type="button"
        variant="secondary"
        className="w-full"
        onClick={handleClick}
        isLoading={isLoading}
      >
        <UserRound className="h-4 w-4" aria-hidden="true" />
        Continue as guest
      </Button>
      <p className="text-center text-caption text-text-secondary">
        Try the placement test right away. No email, no password.
      </p>
      {error && <Alert tone="danger">{error}</Alert>}
    </div>
  );
}
