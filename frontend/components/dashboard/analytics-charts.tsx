"use client"

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"
import { Bar, BarChart, CartesianGrid, Cell, Legend, Line, LineChart, XAxis, YAxis } from "recharts"
import type { DashboardData } from "@/types/dashboard"

interface AnalyticsChartsProps {
  dashboardData: DashboardData
}

export function AnalyticsCharts({ dashboardData }: AnalyticsChartsProps) {
  const { analytics } = dashboardData

  const chartConfigLearningTimeline = {
    lessons: {
      label: "Lessons Completed",
      color: "hsl(var(--chart-1))",
    },
    hours: {
      label: "Hours Spent",
      color: "hsl(var(--chart-2))",
    },
    skills_gained: {
      label: "Skills Gained",
      color: "hsl(var(--chart-3))",
    },
  }

  const chartConfigSkillLevels = {
    level: {
      label: "Skill Level",
      color: "hsl(var(--chart-1))",
    },
  }

  const chartConfigTimeDistribution = {
    hours: {
      label: "Hours",
    },
  }

  const chartConfigCareerProgress = {
    progress_percentage: {
      label: "Progress",
      color: "hsl(var(--chart-1))",
    },
  }

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      {/* Learning Timeline */}
      <Card>
        <CardHeader>
          <CardTitle>Learning Timeline</CardTitle>
          <CardDescription>Lessons, hours, and skills gained over time.</CardDescription>
        </CardHeader>
        <CardContent>
          <ChartContainer config={chartConfigLearningTimeline} className="min-h-[300px] w-full">
            <LineChart accessibilityLayer data={analytics.learning_timeline}>
              <CartesianGrid vertical={false} />
              <XAxis
                dataKey="date"
                tickLine={false}
                tickMargin={10}
                axisLine={false}
                tickFormatter={(value) =>
                  new Date(value).toLocaleDateString("en-US", { month: "short", day: "numeric" })
                }
              />
              <YAxis />
              <ChartTooltip cursor={false} content={<ChartTooltipContent />} />
              <Legend />
              <Line dataKey="lessons" type="monotone" stroke="var(--color-lessons)" strokeWidth={2} dot={false} />
              <Line dataKey="hours" type="monotone" stroke="var(--color-hours)" strokeWidth={2} dot={false} />
              <Line
                dataKey="skills_gained"
                type="monotone"
                stroke="var(--color-skills_gained)"
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ChartContainer>
        </CardContent>
      </Card>

      {/* Skill Levels */}
      <Card>
        <CardHeader>
          <CardTitle>Skill Levels</CardTitle>
          <CardDescription>Your current proficiency across different skills.</CardDescription>
        </CardHeader>
        <CardContent>
          <ChartContainer config={chartConfigSkillLevels} className="min-h-[300px] w-full">
            <BarChart accessibilityLayer data={analytics.skill_levels}>
              <CartesianGrid vertical={false} />
              <XAxis dataKey="skill" tickLine={false} tickMargin={10} axisLine={false} />
              <YAxis />
              <ChartTooltip cursor={false} content={<ChartTooltipContent />} />
              <Bar dataKey="level" fill="var(--color-level)" radius={8} />
            </BarChart>
          </ChartContainer>
        </CardContent>
      </Card>

      {/* Time Distribution */}
      <Card>
        <CardHeader>
          <CardTitle>Time Distribution</CardTitle>
          <CardDescription>How you spend your learning hours.</CardDescription>
        </CardHeader>
        <CardContent>
          <ChartContainer config={chartConfigTimeDistribution} className="min-h-[300px] w-full">
            <BarChart accessibilityLayer data={analytics.time_distribution}>
              <CartesianGrid vertical={false} />
              <XAxis dataKey="activity" tickLine={false} tickMargin={10} axisLine={false} />
              <YAxis />
              <ChartTooltip cursor={false} content={<ChartTooltipContent />} />
              <Bar dataKey="hours" radius={8}>
                {analytics.time_distribution.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ChartContainer>
        </CardContent>
      </Card>

      {/* Career Progress */}
      <Card>
        <CardHeader>
          <CardTitle>Career Progress</CardTitle>
          <CardDescription>Milestones on your career path.</CardDescription>
        </CardHeader>
        <CardContent>
          <ChartContainer config={chartConfigCareerProgress} className="min-h-[300px] w-full">
            <BarChart accessibilityLayer data={analytics.career_progress}>
              <CartesianGrid vertical={false} />
              <XAxis
                dataKey="milestone"
                tickLine={false}
                tickMargin={10}
                axisLine={false}
                angle={-45}
                textAnchor="end"
                height={80}
              />
              <YAxis />
              <ChartTooltip cursor={false} content={<ChartTooltipContent />} />
              <Bar dataKey="progress_percentage" fill="var(--color-progress_percentage)" radius={8} />
            </BarChart>
          </ChartContainer>
        </CardContent>
      </Card>
    </div>
  )
}
