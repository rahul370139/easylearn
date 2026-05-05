"use client"

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import type { DashboardData } from "@/types/dashboard"

interface AchievementsProps {
  dashboardData: DashboardData
}

export function Achievements({ dashboardData }: AchievementsProps) {
  const { achievements } = dashboardData

  return (
    <Card>
      <CardHeader>
        <CardTitle>Achievements</CardTitle>
        <CardDescription>Badges and milestones you've earned.</CardDescription>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-[300px] pr-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {achievements.length > 0 ? (
              achievements.map((achievement, index) => (
                <div key={index} className="flex items-center gap-3 p-3 border rounded-lg">
                  <div className="text-3xl">{achievement.icon}</div>
                  <div>
                    <h4 className="font-medium">{achievement.title}</h4>
                    <p className="text-sm text-muted-foreground">{achievement.description}</p>
                    <Badge variant="secondary" className="mt-1 text-xs">
                      Earned: {achievement.earned_date}
                    </Badge>
                  </div>
                </div>
              ))
            ) : (
              <p className="text-sm text-muted-foreground col-span-2">No achievements unlocked yet.</p>
            )}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  )
}
