import { HTMLAttributes } from "react";
import { cn } from "@/lib/utils";

type Tone = "green" | "blue" | "cream" | "success" | "warning" | "danger" | "neutral";

const toneStyles: Record<Tone, string> = {
  green: "bg-ku-soft-green text-ku-dark-green",
  blue: "bg-ku-light-blue text-ku-dark-green",
  cream: "bg-ku-cream text-text-primary",
  success: "bg-success/15 text-success",
  warning: "bg-warning/15 text-warning",
  danger: "bg-danger/15 text-danger",
  neutral: "bg-border text-text-secondary",
};

export function Badge({
  tone = "neutral",
  className,
  children,
  ...props
}: HTMLAttributes<HTMLSpanElement> & { tone?: Tone }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-badge px-3 py-1 text-caption font-medium",
        toneStyles[tone],
        className
      )}
      {...props}
    >
      {children}
    </span>
  );
}
