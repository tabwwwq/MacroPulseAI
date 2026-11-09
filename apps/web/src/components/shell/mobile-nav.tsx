"use client";

import * as Dialog from "@radix-ui/react-dialog";
import { X } from "lucide-react";

import { Sidebar } from "@/components/shell/sidebar";

interface MobileNavProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

/** Off-canvas navigation for < lg screens. Focus-trapped, Esc to close, closes on navigation. */
export function MobileNav({ open, onOpenChange }: MobileNavProps) {
  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden" />
        <Dialog.Content
          className="fixed inset-y-0 left-0 z-50 w-72 max-w-[85vw] border-r border-line bg-surface shadow-card focus:outline-none lg:hidden"
          aria-describedby={undefined}
        >
          <Dialog.Title className="sr-only">Navigation</Dialog.Title>
          <Dialog.Close
            className="absolute right-3 top-3 inline-flex size-8 items-center justify-center rounded-lg text-fg-muted hover:bg-surface-2 hover:text-fg"
            aria-label="Close navigation"
          >
            <X className="size-4" aria-hidden />
          </Dialog.Close>
          <Sidebar onNavigate={() => onOpenChange(false)} />
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
