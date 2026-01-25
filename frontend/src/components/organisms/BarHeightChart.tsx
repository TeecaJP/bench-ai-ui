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
  description = "Bar position during workout"
}: BarHeightChartProps) {
  // Filter and find the baseline (maximum Y value = chest level)
  const validPoints = data.filter((point) => point.barDetected && point.barY !== null)

  if (validPoints.length === 0) {
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

  // Find max barY to use as chest baseline
  const maxBarY = Math.max(...validPoints.map(p => p.barY as number))

  // Transform data for recharts - height from chest
  const chartData = validPoints.map((point) => ({
    timestamp: point.timestamp, // number for numeric axis
    barHeight: Math.max(0, maxBarY - (point.barY as number)),
  }))

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
          <LineChart
            data={chartData}
            margin={{ top: 20, right: 30, left: 20, bottom: 20 }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="timestamp"
              type="number"
              domain={[0, 'auto']}
              label={{ value: 'Time (s)', position: 'insideBottom', offset: -5 }}
            />
            <YAxis
              width={80}
              label={{ value: 'Bar Height (px)', angle: -90, position: 'insideLeft', offset: 0 }}
              padding={{ top: 20, bottom: 20 }}
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
