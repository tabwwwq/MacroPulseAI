import Link from "next/link";

import { buttonVariants } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/states";

export default function NotFound() {
  return (
    <EmptyState
      className="mt-10"
      title="Page not found"
      action={
        <Link href="/" className={buttonVariants({ size: "sm" })}>
          Back to overview
        </Link>
      }
    >
      The page you requested does not exist.
    </EmptyState>
  );
}
