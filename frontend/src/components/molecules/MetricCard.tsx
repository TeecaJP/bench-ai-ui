"use client"

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/atoms/Card"
import { Activity, AlertTriangle, CheckCircle2 } from "lucide-react"

interface AnalysisMetric {
  label: string
  value: string | number
  trend?: "up" | "down" | "neutral"
}

interface MetricCardProps {
  title: string
  description?: string
  metrics: AnalysisMetric[]
  status?: "success" | "warning" | "info"
}

export function MetricCard({ title, description, metrics, status = "info" }: MetricCardProps) {
  const Icon = status === "success" ? CheckCircle2 : status === "warning" ? AlertTriangle : Activity
  const iconColor = status === "success" ? "text-green-500" : status === "warning" ? "text-yellow-500" : "text-blue-500"

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Icon className={`h-5 w-5 ${iconColor}`} />
          {title}
        </CardTitle>
        {description && <CardDescription>{description}</CardDescription>}
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {metrics.map((metric, idx) => (
            <div key={idx} className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">{metric.label}</span>
              <span className="text-sm font-medium">{metric.value}</span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
