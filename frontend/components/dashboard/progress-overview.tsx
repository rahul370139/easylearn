"use client"

import { Card, CardContent } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { BookOpen, Clock, Flame, Target } from "lucide-react"
import type { DashboardData } from "@/types/dashboard"

interface ProgressOverviewProps {
  dashboardData: DashboardData
}

export function ProgressOverview({ dashboardData }: ProgressOverviewProps) {
  const { progress } = dashboardData

  return (
    <>
      <Card className="relative overflow-hidden">
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Learning Progress</p>
              <p className="text-2xl font-bold">{progress.completion_percentage}%</p>
              <p className="text-xs text-muted-foreground mt-1">
                {progress.completed_lessons}/{progress.total_lessons} lessons
              </p>
            </div>
            <BookOpen className="h-8 w-8 text-blue-500" />
          </div>
          <Progress value={progress.completion_percentage} className="mt-4" />
        </CardContent>
      </Card>

      <Card className="relative overflow-hidden">
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Time Spent</p>
              <p className="text-2xl font-bold">{progress.hours_spent}h</p>
              <p className="text-xs text-muted-foreground mt-1">Total learning time</p>
            </div>
            <Clock className="h-8 w-8 text-green-500" />
          </div>
        </CardContent>
      </Card>

      <Card className="relative overflow-hidden">
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Current Streak</p>
              <p className="text-2xl font-bold flex items-center gap-1">🔥 {progress.current_streak}</p>
              <p className="text-xs text-muted-foreground mt-1">days in a row</p>
            </div>
            <Flame className="h-8 w-8 text-orange-500" />
          </div>
        </CardContent>
      </Card>

      <Card className="relative overflow-hidden">
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Career Progress</p>
              <p className="text-2xl font-bold">{progress.career_advancement_percentage}%</p>
              <p className="text-xs text-muted-foreground mt-1">to {progress.next_milestone}</p>
            </div>
            <Target className="h-8 w-8 text-purple-500" />
          </div>
          <Progress value={progress.career_advancement_percentage} className="mt-4" />
        </CardContent>
      </Card>
    </>
  )
}
