"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { BookOpen, Briefcase, AlertTriangle, TrendingUp, ArrowRight } from "lucide-react"
import type { DashboardData } from "@/types/dashboard"
import Link from "next/link"

interface RecommendationsProps {
  dashboardData: DashboardData
}

export function Recommendations({ dashboardData }: RecommendationsProps) {
  const { recommendations } = dashboardData

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Next Lessons */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BookOpen className="h-5 w-5" />
            Recommended Lessons
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {recommendations.next_lessons.length > 0 ? (
              recommendations.next_lessons.map((lesson, index) => (
                <div key={index} className="p-4 border rounded-lg">
                  <div className="flex items-start justify-between mb-2">
                    <h4 className="font-medium">{lesson.title}</h4>
                    <Badge variant="outline" className="text-xs">
                      Priority {lesson.priority}
                    </Badge>
                  </div>
                  <p className="text-sm text-muted-foreground mb-3">{lesson.description}</p>
                  <div className="flex items-center justify-between">
                    <div className="flex gap-2">
                      <Badge variant="secondary" className="text-xs">
                        {lesson.difficulty}
                      </Badge>
                      <Badge variant="outline" className="text-xs">
                        {lesson.estimated_time}
                      </Badge>
                    </div>
                    <Button size="sm" variant="outline" asChild>
                      <Link href={`/learn?lessonId=${lesson.id}`}>Start Learning</Link>
                    </Button>
                  </div>
                </div>
              ))
            ) : (
              <p className="text-sm text-muted-foreground">No new lesson recommendations.</p>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Career Opportunities */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Briefcase className="h-5 w-5" />
            Career Opportunities
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {recommendations.career_opportunities.length > 0 ? (
              recommendations.career_opportunities.map((opportunity, index) => (
                <div key={index} className="p-4 border rounded-lg">
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <h4 className="font-medium">{opportunity.title}</h4>
                      <p className="text-sm text-muted-foreground">{opportunity.company}</p>
                    </div>
                    <Badge variant="default" className="text-xs">
                      {opportunity.match_score}% Match
                    </Badge>
                  </div>
                  <p className="text-sm font-medium text-green-600 mb-2">{opportunity.salary_range}</p>
                  <p className="text-xs text-muted-foreground mb-3">{opportunity.location}</p>
                  <div className="flex flex-wrap gap-1 mb-3">
                    {opportunity.skills_required.map((skill, skillIndex) => (
                      <Badge key={skillIndex} variant="outline" className="text-xs">
                        {skill}
                      </Badge>
                    ))}
                  </div>
                  <Button size="sm" variant="outline" className="w-full bg-transparent">
                    View Details
                  </Button>
                </div>
              ))
            ) : (
              <p className="text-sm text-muted-foreground">No career opportunities found.</p>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Skill Gaps */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-orange-500" />
            Skill Gaps to Address
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {recommendations.skill_gaps.length > 0 ? (
              recommendations.skill_gaps.map((gap, index) => (
                <div key={index} className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="font-medium">{gap.skill}</span>
                    <div className="flex gap-2">
                      <Badge
                        variant={
                          gap.priority === "high" ? "destructive" : gap.priority === "medium" ? "default" : "secondary"
                        }
                        className="text-xs"
                      >
                        {gap.priority}
                      </Badge>
                      <Badge variant="outline" className="text-xs">
                        {gap.market_demand}
                      </Badge>
                    </div>
                  </div>
                  <Progress value={(gap.current_level / gap.target_level) * 100} />
                  <p className="text-sm text-muted-foreground">
                    Level {gap.current_level} → {gap.target_level} (Market: {gap.market_demand})
                  </p>
                </div>
              ))
            ) : (
              <p className="text-sm text-muted-foreground">No significant skill gaps detected.</p>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Market Trends */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            Market Trends
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {recommendations.market_trends.length > 0 ? (
              recommendations.market_trends.map((trend, index) => (
                <div key={index} className="p-4 border rounded-lg">
                  <div className="flex items-start justify-between mb-2">
                    <h4 className="font-medium">{trend.trend}</h4>
                    <div className="flex gap-2">
                      <Badge variant="default" className="text-xs">
                        {trend.growth_rate}
                      </Badge>
                      <Badge variant="outline" className="text-xs">
                        {trend.relevance_score}% relevant
                      </Badge>
                    </div>
                  </div>
                  <p className="text-sm text-muted-foreground">{trend.description}</p>
                </div>
              ))
            ) : (
              <p className="text-sm text-muted-foreground">No market trends available.</p>
            )}
          </div>
        </CardContent>
      </Card>

      {/* General Recommendations */}
      <Card className="lg:col-span-2">
        <CardHeader>
          <CardTitle>General Recommendations</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4">
          {recommendations.general_recommendations.length > 0 ? (
            recommendations.general_recommendations.map((rec) => (
              <div key={rec.id} className="flex items-center justify-between">
                <div>
                  <div className="font-medium">{rec.title}</div>
                  <div className="text-sm text-muted-foreground">{rec.description}</div>
                </div>
                <Button variant="ghost" size="icon" asChild>
                  <Link href={rec.link}>
                    <ArrowRight className="h-4 w-4" />
                    <span className="sr-only">View {rec.title}</span>
                  </Link>
                </Button>
              </div>
            ))
          ) : (
            <p className="text-sm text-muted-foreground">No general recommendations available.</p>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
