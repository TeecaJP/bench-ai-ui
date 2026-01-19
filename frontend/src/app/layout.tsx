import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css"
import { Header } from "@/components/organisms/Header"

const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "Workout Analysis - Bench Press Form Analyzer",
  description: "Analyze your bench press form using computer vision",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={`${inter.className} h-screen overflow-hidden`}>
        <div className="h-full flex flex-col">
          <Header />
          <main className="flex-1 overflow-hidden">{children}</main>
        </div>
      </body>
    </html>
  )
}
