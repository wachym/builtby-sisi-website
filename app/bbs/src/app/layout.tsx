import type { Metadata, Viewport } from "next";
import { Instrument_Serif, Manrope } from "next/font/google";
import "./globals.css";

const manrope = Manrope({
  variable: "--font-manrope",
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700"],
});

const instrumentSerif = Instrument_Serif({
  variable: "--font-instrument-serif",
  subsets: ["latin"],
  weight: "400",
  style: ["normal", "italic"],
});

export const viewport: Viewport = {
  themeColor: "#2b2d57",
  colorScheme: "light",
};

export const metadata: Metadata = {
  title: "Built By Sisi — Software Engineering Studio",
  description:
    "Built By Sisi — bespoke software engineering. We design and ship reliable products, platforms, and integrations for teams who care about craft.",
  openGraph: {
    title: "Built By Sisi — Software Engineering Studio",
    description:
      "Thoughtful engineering for serious products. We design, build, and evolve software that stays fast, maintainable, and aligned with your business.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${manrope.variable} ${instrumentSerif.variable}`}>
      <body>{children}</body>
    </html>
  );
}
