"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Button } from "@/components/ui/button"
import { Flame, TrendingUp, BookOpen, Play } from "lucide-react"

interface DashboardStatsProps {
  data: {
    overallCompletion: number
    currentStreak: number
    skillGaps: Array<{
      skill: string
      current: number
      target: number
    }>
    recentLessons: Array<{
      id: string
      title: string
      progress: number
      lastAccessed: string | null
    }>
  }
}

export function DashboardStats({ data }: DashboardStatsProps) {
  return (
    <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
      {/* Overall Progress */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Overall Progress</CardTitle>
          <TrendingUp className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{data.overallCompletion}%</div>
          <Progress value={data.overallCompletion} className="mt-2" />
          <p className="text-xs text-muted-foreground mt-2">Keep going! You're making great progress.</p>
        </CardContent>
      </Card>

      {/* Current Streak */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Current Streak</CardTitle>
          <Flame className="h-4 w-4 text-orange-500" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold flex items-center gap-2">🔥 {data.currentStreak} days</div>
          <p className="text-xs text-muted-foreground mt-2">Amazing consistency! Keep it up.</p>
        </CardContent>
      </Card>

      {/* Skill Gaps */}
      <Card className="md:col-span-2 lg:col-span-1">
        <CardHeader>
          <CardTitle className="text-sm font-medium">Skill Development</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {data.skillGaps.slice(0, 3).map((skill) => (
            <div key={skill.skill} className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span>{skill.skill}</span>
                <span className="text-muted-foreground">
                  {skill.current}% / {skill.target}%
                </span>
              </div>
              <Progress value={skill.current} className="h-2" />
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Recent Lessons */}
      <Card className="md:col-span-2">
        <CardHeader>
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <BookOpen className="h-4 w-4" />
            Recent Lessons
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {data.recentLessons.map((lesson) => (
            <div
              key={lesson.id}
              className="flex items-center justify-between p-3 rounded-lg bg-muted/50 hover:bg-muted transition-colors"
            >
              <div className="flex-1">
                <h4 className="font-medium text-sm">{lesson.title}</h4>
                <div className="flex items-center gap-2 mt-1">
                  <Progress value={lesson.progress} className="h-1 flex-1 max-w-24" />
                  <span className="text-xs text-muted-foreground">{lesson.progress}%</span>
                </div>
              </div>
              <Button size="sm" variant="outline">
                <Play className="h-3 w-3 mr-1" />
                {lesson.progress > 0 ? "Continue" : "Start"}
              </Button>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  )
}
