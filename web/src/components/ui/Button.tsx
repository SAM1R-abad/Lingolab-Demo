import { ButtonHTMLAttributes, forwardRef } from "react";
import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

type Variant = "primary" | "secondary" | "accent" | "danger" | "ghost";
type Size = "sm" | "md" | "lg";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  isLoading?: boolean;
}

const variantStyles: Record<Variant, string> = {
  // Primary - KU Green, white text
  primary: "bg-ku-green text-white hover:bg-ku-dark-green disabled:bg-text-secondary/40",
  // Secondary - outline, transparent background
  secondary:
    "bg-transparent text-ku-green border border-ku-green hover:bg-ku-soft-green/40 disabled:text-text-secondary/50 disabled:border-border",
  // Accent - Gold
  accent: "bg-[#D4A017] text-white hover:bg-[#B4870F] disabled:bg-text-secondary/40",
  // Danger - Red
  danger: "bg-danger text-white hover:bg-danger/90 disabled:bg-text-secondary/40",
  ghost: "bg-transparent text-text-primary hover:bg-background disabled:text-text-secondary/50",
};

const sizeStyles: Record<Size, string> = {
  sm: "h-9 px-3 text-small",
  md: "h-11 px-4 text-body",
  lg: "h-12 px-6 text-body",
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "primary", size = "md", isLoading, disabled, children, ...props }, ref) => {
    return (
      <button
        ref={ref}
        disabled={disabled || isLoading}
        className={cn(
          "inline-flex items-center justify-center gap-2 rounded-button font-medium transition-colors",
          "disabled:cursor-not-allowed",
          variantStyles[variant],
          sizeStyles[size],
          className
        )}
        {...props}
      >
        {isLoading && <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />}
        {children}
      </button>
    );
  }
);
Button.displayName = "Button";
