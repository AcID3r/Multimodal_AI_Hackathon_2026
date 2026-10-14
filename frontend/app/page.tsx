"use client";
import { useEffect, useRef } from "react";
export default function Home() {
  const host = useRef<HTMLDivElement>(null);
  useEffect(() => {
    let dispose: (() => void) | undefined;
    let cancelled = false;
    const moduleUrl = "/dashboard.js";
    import(/* webpackIgnore: true */ moduleUrl).then(({ mountDashboard }) => {
      if (!cancelled && host.current) dispose = mountDashboard(host.current, process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000");
    });
    return () => { cancelled = true; dispose?.(); };
  }, []);
  return <main ref={host}>
    <div className="app-loading" role="status">
      {/* A native image matches the dependency-free dashboard's original logo. */}
      <img src="/cadence-logo.png" width="144" height="96" alt="Cadence logo" />
      <p>Opening the speech lab...</p>
    </div>
  </main>;
}
