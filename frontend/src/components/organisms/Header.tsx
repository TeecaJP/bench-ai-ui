"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { Video, Upload } from "lucide-react"

export function Header() {
  const pathname = usePathname()

  const isActive = (path: string) => {
    if (path === '/') {
      return pathname === '/'
    }
    return pathname?.startsWith(path)
  }

  return (
    <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-16 items-center px-4">
        <div className="mr-8 flex items-center space-x-2">
          <Video className="h-6 w-6" />
          <span className="text-xl font-bold">Workout Analyzer</span>
        </div>
        
        <nav className="flex items-center space-x-6 text-sm font-medium">
          <Link
            href="/"
            className={`transition-colors hover:text-foreground/80 ${
              isActive('/') && !isActive('/videos')
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
            className={`transition-colors hover:text-foreground/80 ${
              isActive('/videos')
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
    </header>
  )
}
