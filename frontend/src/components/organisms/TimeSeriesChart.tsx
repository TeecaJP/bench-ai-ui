"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/atoms/Card"
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts"
import type { TimeSeriesDataPoint } from "@/lib/api"
import { TrendingUp } from "lucide-react"

interface TimeSeriesChartProps {
  data: TimeSeriesDataPoint[]
  title?: string
  description?: string
}

export function TimeSeriesChart({ data, title = "Movement Analysis", description }: TimeSeriesChartProps) {
  // Transform data for recharts
  const chartData = data.map((point) => ({
    timestamp: point.timestamp.toFixed(2),
    hip: point.hipY,
    elbow: point.elbowY,
    shoulder: point.shoulderY,
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
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="timestamp" 
              label={{ value: 'Time (s)', position: 'insideBottom', offset: -5 }}
            />
            <YAxis 
              label={{ value: 'Y Position (px)', angle: -90, position: 'insideLeft' }}
            />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="hip" stroke="#8884d8" name="Hip" strokeWidth={2} />
            <Line type="monotone" dataKey="elbow" stroke="#82ca9d" name="Elbow" strokeWidth={2} />
            <Line type="monotone" dataKey="shoulder" stroke="#ffc658" name="Shoulder" strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}
