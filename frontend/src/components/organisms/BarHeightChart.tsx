"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/atoms/Card"
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts"
import type { TimeSeriesDataPoint } from "@/lib/api"
import { TrendingUp } from "lucide-react"

interface BarHeightChartProps {
  data: TimeSeriesDataPoint[]
  title?: string
  description?: string
}

export function BarHeightChart({ 
  data, 
  title = "Bar Height Over Time", 
  description = "Bar position during workout (lower values = bar closer to chest)"
}: BarHeightChartProps) {
  // Filter and transform data for recharts - only include frames where bar is detected
  const chartData = data
    .filter((point) => point.barDetected && point.barY !== null)
    .map((point) => ({
      timestamp: point.timestamp.toFixed(2),
      barHeight: point.barY,
    }))

  if (chartData.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            {title}
          </CardTitle>
          {description && <CardDescription>{description}</CardDescription>}
        </CardHeader>
        <CardContent>
          <div className="h-[300px] flex items-center justify-center text-muted-foreground">
            No bar position data available
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <TrendingUp className="h-5 w-5" />
          {title}
        </CardTitle>
        {description && <CardDescription>{description}</CardDescription>}
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="timestamp" 
              label={{ value: 'Time (s)', position: 'insideBottom', offset: -5 }}
            />
            <YAxis 
              label={{ value: 'Bar Height (px)', angle: -90, position: 'insideLeft' }}
              reversed
            />
            <Tooltip />
            <Legend />
            <Line 
              type="monotone" 
              dataKey="barHeight" 
              stroke="#ff6b6b" 
              name="Bar Height" 
              strokeWidth={2}
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}
