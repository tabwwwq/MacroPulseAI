import { cva, type VariantProps } from "class-variance-authority";
import type { ButtonHTMLAttributes } from "react";

import { cn } from "@/lib/cn";

export const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-lg text-sm font-medium transition-[background-color,border-color,color,box-shadow,filter,transform] duration-200 active:translate-y-px disabled:pointer-events-none disabled:opacity-50 [&_svg]:size-4 [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        primary:
          "bg-gradient-to-b from-[#7ad6ff] to-accent-strong font-semibold text-canvas shadow-[inset_0_1px_0_rgb(255_255_255/0.45),0_10px_28px_-10px_rgb(47_155_255/0.75)] hover:brightness-110",
        secondary:
          "border border-line-strong bg-surface-2 text-fg shadow-[inset_0_1px_0_rgb(255_255_255/0.05)] hover:border-accent/45 hover:bg-elevated",
        ghost: "text-fg-muted hover:bg-surface-2 hover:text-fg",
      },
      size: {
        sm: "h-8 px-3",
        md: "h-9 px-4",
        icon: "size-9",
      },
    },
    defaultVariants: { variant: "secondary", size: "md" },
  },
);

export interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

export function Button({ className, variant, size, type = "button", ...props }: ButtonProps) {
  return <button type={type} className={cn(buttonVariants({ variant, size }), className)} {...props} />;
}
