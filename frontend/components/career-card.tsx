"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { TrendingUp } from "lucide-react"

interface CareerCardProps {
  career: {
    id: string
    title: string
    icon: string
    salaryRange: string
    matchScore: number
    description: string
  }
  onViewProfile: (careerId: string) => void
}

export function CareerCard({ career, onViewProfile }: CareerCardProps) {
  return (
    <Card className="group hover:shadow-lg transition-all duration-300 hover:-translate-y-1">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl">{career.icon}</span>
            <div>
              <CardTitle className="text-lg group-hover:text-primary transition-colors">{career.title}</CardTitle>
              <p className="text-sm text-muted-foreground mt-1">{career.description}</p>
            </div>
          </div>
          <Badge variant="secondary" className="flex items-center gap-1">
            <TrendingUp className="h-3 w-3" />
            {career.matchScore}%
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium">Salary Range</span>
          <span className="text-sm text-muted-foreground">{career.salaryRange}</span>
        </div>

        <Button className="w-full" onClick={() => onViewProfile(career.id)}>
          View Career Profile
        </Button>
      </CardContent>
    </Card>
  )
}
