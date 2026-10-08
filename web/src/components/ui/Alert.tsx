import { AlertCircle, CheckCircle2, Info } from "lucide-react";
import { cn } from "@/lib/utils";

type Tone = "danger" | "success" | "info";

const toneStyles: Record<Tone, string> = {
  danger: "bg-danger/10 text-danger border-danger/30",
  success: "bg-success/10 text-success border-success/30",
  info: "bg-ku-light-blue/40 text-ku-dark-green border-ku-light-blue",
};

const toneIcons: Record<Tone, typeof AlertCircle> = {
  danger: AlertCircle,
  success: CheckCircle2,
  info: Info,
};

export function Alert({ tone = "info", children }: { tone?: Tone; children: React.ReactNode }) {
  const Icon = toneIcons[tone];
  return (
    <div
      role="alert"
      className={cn(
        "flex items-start gap-2 rounded-input border px-3 py-2 text-small",
        toneStyles[tone]
      )}
    >
      <Icon className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
      <span>{children}</span>
    </div>
  );
}
