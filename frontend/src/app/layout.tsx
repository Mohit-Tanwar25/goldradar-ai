import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Gold Contract Radar — MCX Commodity Derivatives Intelligence",
  description: "Understand MCX gold prices, compare contracts, and evaluate historical opportunities after costs.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full flex flex-col bg-[#F7F8FA] text-[#17191D]">
        {children}
      </body>
    </html>
  );
}
