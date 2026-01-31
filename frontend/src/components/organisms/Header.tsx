"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { useTranslation } from "@/hooks/useTranslation"
import { Video, Upload, Languages } from "lucide-react"

export function Header() {
  const pathname = usePathname()
  const { language, setLanguage } = useTranslation()

  const isActive = (path: string) => {
    if (path === '/') {
      return pathname === '/'
    }
    return pathname?.startsWith(path)
  }

  return (
    <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-16 items-center px-4 justify-between">
        <div className="flex items-center">
          <div className="mr-8 flex items-center space-x-2">
            <Video className="h-6 w-6" />
            <span className="text-xl font-bold">Workout Analyzer</span>
          </div>

          <nav className="flex items-center space-x-6 text-sm font-medium">
            <Link
              href="/"
              className={`transition-colors hover:text-foreground/80 ${isActive('/') && !isActive('/videos')
                  ? 'text-foreground'
                  : 'text-foreground/60'
                }`}
            >
              <div className="flex items-center gap-2">
                <Upload className="h-4 w-4" />
                Upload
              </div>
            </Link>

            <Link
              href="/videos"
              className={`transition-colors hover:text-foreground/80 ${isActive('/videos')
                  ? 'text-foreground'
                  : 'text-foreground/60'
                }`}
            >
              <div className="flex items-center gap-2">
                <Video className="h-4 w-4" />
                Library
              </div>
            </Link>
          </nav>
        </div>

        {/* Language Switcher */}
        <div className="flex items-center gap-2">
          <Languages className="h-4 w-4 text-muted-foreground" />
          <div className="flex items-center border rounded-md overflow-hidden text-xs font-medium">
            <button
              onClick={() => setLanguage('en')}
              className={`px-3 py-1.5 transition-colors ${language === 'en' ? 'bg-primary text-primary-foreground' : 'hover:bg-muted'}`}
            >
              EN
            </button>
            <div className="w-[1px] h-full bg-border"></div>
            <button
              onClick={() => setLanguage('ja')}
              className={`px-3 py-1.5 transition-colors ${language === 'ja' ? 'bg-primary text-primary-foreground' : 'hover:bg-muted'}`}
            >
              JP
            </button>
          </div>
        </div>
      </div>
    </header>
  )
}
