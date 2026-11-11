import Link from "next/link";

export function LogoMark({ className }: { className?: string }) {
  return (
    // Solid stroke on purpose: an SVG gradient referenced by id breaks when the first instance
    // with that id sits inside a display:none subtree (e.g. the desktop sidebar on mobile).
    <svg viewBox="0 0 32 32" className={className} aria-hidden>
      <rect x="1" y="1" width="30" height="30" rx="9" fill="#101a30" stroke="#3a5a86" />
      <rect x="1.5" y="1.5" width="29" height="14" rx="8.5" fill="#4cc3ff" opacity="0.08" />
      <path
        d="M5 18.5h5.2l2.3-6.2 3.6 11 3.1-14.6 2.6 9.8H27"
        fill="none"
        stroke="#4cc3ff"
        strokeWidth="2.2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function Logo({ onNavigate }: { onNavigate?: () => void }) {
  return (
    <Link
      href="/"
      onClick={onNavigate}
      className="flex items-center gap-2.5 rounded-lg outline-offset-4"
      aria-label="MacroPulse AI — overview"
    >
      <LogoMark className="size-8 drop-shadow-[0_0_10px_rgb(76_195_255/0.45)]" />
      <span className="flex items-baseline gap-1.5">
        <span className="text-headline text-[15px] font-semibold tracking-tight">MacroPulse</span>
        <span className="rounded border border-accent/30 bg-accent/10 px-1 font-mono text-[10px] font-medium text-accent">
          AI
        </span>
      </span>
    </Link>
  );
}
