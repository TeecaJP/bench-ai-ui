"use client"

import * as React from "react"

interface TabsProps {
  defaultValue: string
  children: React.ReactNode
  className?: string
}

interface TabsListProps {
  children: React.ReactNode
  className?: string
}

interface TabsTriggerProps {
  value: string
  children: React.ReactNode
  className?: string
}

interface TabsContentProps {
  value: string
  children: React.ReactNode
  className?: string
}

const TabsContext = React.createContext<{
  value: string
  setValue: (value: string) => void
}>({ value: "", setValue: () => { } })

export function Tabs({ defaultValue, children, className }: TabsProps) {
  const [value, setValue] = React.useState(defaultValue)
  return (
    <TabsContext.Provider value={{ value, setValue }}>
      <div className={className}>{children}</div>
    </TabsContext.Provider>
  )
}

export function TabsList({ children, className }: TabsListProps) {
  return (
    <div className={`flex gap-1 border-b p-1 ${className || ""}`}>
      {children}
    </div>
  )
}

export function TabsTrigger({ value, children, className }: TabsTriggerProps) {
  const context = React.useContext(TabsContext)
  const isActive = context.value === value

  return (
    <button
      onClick={() => context.setValue(value)}
      className={`px-4 py-2 text-sm font-medium transition-all rounded-md
        ${isActive
          ? "bg-primary text-primary-foreground shadow-sm"
          : "text-muted-foreground hover:bg-muted hover:text-foreground"} 
        ${className || ""}`}
    >
      {children}
    </button>
  )
}

export function TabsContent({ value, children, className }: TabsContentProps) {
  const context = React.useContext(TabsContext)
  if (context.value !== value) return null
  return <div className={`pt-4 animate-in fade-in duration-200 ${className || ""}`}>{children}</div>
}
