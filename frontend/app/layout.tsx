import type { Metadata } from "next";
import "../public/dashboard.css";

export const metadata: Metadata = {
  title: "Cadence | The Speech Lab",
  description: "Find your rhythm. Understand your delivery. Cadence turns speech comparisons into focused practice.",
  icons: {
    icon: [{ url: "/cadence-logo.png", type: "image/png" }],
    apple: "/cadence-logo.png",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="en"><body>{children}</body></html>;
}
