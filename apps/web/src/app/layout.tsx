import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "DataInsight AI",
  description: "Convierte tus datos en insights con IA",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es">
      <body className="bg-gray-950 text-gray-50 antialiased">{children}</body>
    </html>
  );
}
