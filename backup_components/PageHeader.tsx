import { ReactNode } from "react";

export function PageHeader({ title, subtitle, action }: { title: string; subtitle?: string; action?: ReactNode }) {
  return (
    <div className="mb-10 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between animate-in fade-in duration-700">
      <div>
        <h1 className="text-3xl font-black italic uppercase tracking-tighter text-black">
          {title}
        </h1>
        {subtitle ? (
          <p className="text-sm font-bold tracking-widest uppercase text-black/40 mt-1">
            {subtitle}
          </p>
        ) : null}
      </div>
      {action ? <div className="z-10">{action}</div> : null}
    </div>
  );
}
