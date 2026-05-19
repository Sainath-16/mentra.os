import Link from "next/link";

export function PublicNav() {
  return (
    <header className="sticky top-0 z-30 border-b bg-white/80 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-6">
        <Link href="/" className="text-sm font-extrabold tracking-tight text-slate-900">
          MENTRA
        </Link>
        <nav className="flex items-center gap-2">
          <Link href="/login" className="rounded-xl px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50">
            Login
          </Link>
          <Link href="/register" className="rounded-xl bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800">
            Register
          </Link>
        </nav>
      </div>
    </header>
  );
}
