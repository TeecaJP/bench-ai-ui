import { Badge } from "@/components/atoms/Badge"
import { cn } from "@/lib/utils"

interface StatusBadgeProps {
  status: string
  className?: string
}

export function StatusBadge({ status, className }: StatusBadgeProps) {
  const getVariant = (status: string) => {
    if (status === "OK" || status === "GOOD REP") return "default"
    if (status.includes("FAIL")) return "destructive"
    if (status === "COMPLETED") return "default"
    if (status === "PENDING") return "secondary"
    if (status === "PROCESSING") return "outline"
    return "secondary"
  }

  return (
    <Badge variant={getVariant(status)} className={cn(className)}>
      {status}
    </Badge>
  )
}
