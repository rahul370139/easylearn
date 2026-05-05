"use client"

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { BookOpen, Brain, Code, MessageSquare, Award, Briefcase } from "lucide-react"
import type { DashboardData } from "@/types/dashboard"

interface RecentActivityProps {
  dashboardData: DashboardData
}

export function RecentActivity({ dashboardData }: RecentActivityProps) {
  const { recent_activity } = dashboardData

  const getActivityIcon = (type: string) => {
    switch (type) {
      case "lesson":
        return <BookOpen className="h-4 w-4 text-blue-500" />
      case "quiz":
        return <Brain className="h-4 w-4 text-green-500" />
      case "project":
        return <Code className="h-4 w-4 text-purple-500" />
      case "chat":
        return <MessageSquare className="h-4 w-4 text-orange-500" />
      case "certificate":
        return <Award className="h-4 w-4 text-yellow-500" />
      case "career":
        return <Briefcase className="h-4 w-4 text-indigo-500" />
      default:
        return null
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent Activity</CardTitle>
        <CardDescription>Your latest interactions and milestones.</CardDescription>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-[300px] pr-4">
          <div className="space-y-4">
            {recent_activity.length > 0 ? (
              recent_activity.map((activity, index) => (
                <div key={index} className="flex items-center gap-4">
                  <div className="flex-shrink-0">{getActivityIcon(activity.type)}</div>
                  <div className="flex-grow">
                    <p className="font-medium">{activity.title}</p>
                    <p className="text-sm text-muted-foreground">
                      {activity.type === "lesson" && activity.progress !== undefined && (
                        <span>Progress: {activity.progress}% - </span>
                      )}
                      {activity.status && (
                        <Badge
                          variant={
                            activity.status === "completed"
                              ? "default"
                              : activity.status === "in_progress"
                                ? "secondary"
                                : "outline"
                          }
                          className="mr-1"
                        >
                          {activity.status.replace(/_/g, " ")}
                        </Badge>
                      )}
                      on {activity.date}
                    </p>
                  </div>
                </div>
              ))
            ) : (
              <p className="text-sm text-muted-foreground">No recent activity to display.</p>
            )}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  )
}
