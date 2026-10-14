import type { Metadata } from "next";
import "../public/dashboard.css";
export const metadata: Metadata = { title: "Cadence | Speech Analytics", description: "Compare speech delivery with measured acoustic evidence." };
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="en"><body>{children}</body></html>;
}
