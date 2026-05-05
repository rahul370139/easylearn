"use client"

import { useState, useEffect, useCallback } from "react"
import { dashboardAPI, userAPI, recommendationAPI, learnAPI } from "@/lib/api"
import { useSession } from "@supabase/auth-helpers-react"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { ProgressOverview } from "@/components/dashboard/progress-overview"
import { RecentActivity } from "@/components/dashboard/recent-activity"
import { Achievements } from "@/components/dashboard/achievements"
import { Recommendations } from "@/components/dashboard/recommendations"
import { AnalyticsCharts } from "@/components/dashboard/analytics-charts"
import { RefreshCw } from "lucide-react"
import { toast } from "@/components/ui/use-toast"
import type { DashboardData } from "@/types/dashboard"
import { Suspense } from "react"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Settings, LogOut } from "lucide-react"

// API Functions with error handling
const updateUserRole = async (userId: string, role: string) => {
  try {
    return await userAPI.updateUserRole(userId, role)
  } catch (error) {
    console.error("Error updating user role:", error)
    return null
  }
}

const completeLesson = async (lessonId: string, userId: string, progressPercentage = 100.0) => {
  try {
    return await learnAPI.completeLesson(lessonId, userId, progressPercentage)
  } catch (error) {
    console.error("Error completing lesson:", error)
    return null
  }
}

const getUserProgress = async (userId: string) => {
  try {
    return await dashboardAPI.getUserProgress(userId)
  } catch (error) {
    console.error("Error getting user progress:", error)
    return null
  }
}

const getRecommendations = async (userId: string, userRole: string, completedLessons: string[] = []) => {
  try {
    return await recommendationAPI.getGeneralRecommendations({
      user_id: userId,
      user_role: userRole,
      completed_lessons: completedLessons,
    })
  } catch (error) {
    console.error("Error getting recommendations:", error)
    return null
  }
}

// Mock data generator function
const generateMockData = (): DashboardData => ({
  progress: {
    lessons_completed: 24,
    total_lessons: 100,
    completion_percentage: 24,
    hours_spent: 67.5,
    current_streak: 12,
    skills_learned: 15,
    career_advancement_percentage: 35,
    current_level: 3,
    next_milestone: "Intermediate Developer",
  },
  recent_activity: [
    {
      type: "lesson",
      title: "Advanced React Patterns",
      date: "2024-01-15",
      progress: 100,
      status: "completed",
    },
    { type: "quiz", title: "JavaScript ES6 Assessment", date: "2024-01-14", progress: 92, status: "completed" },
    { type: "chat", title: "AI Discussion on State Management", date: "2024-01-13", status: "active" },
    {
      type: "lesson",
      title: "Node.js Authentication",
      date: "2024-01-12",
      progress: 75,
      status: "in_progress",
    },
    {
      type: "project",
      title: "Full Stack E-commerce App",
      date: "2024-01-11",
      progress: 45,
      status: "in_progress",
    },
    { type: "certificate", title: "React Fundamentals Certificate", date: "2024-01-10", status: "earned" },
  ],
  achievements: [
    {
      title: "First Steps",
      description: "Completed your first lesson",
      earned_date: "2024-01-01",
      badge_type: "bronze",
      icon: "🎯",
    },
    {
      title: "Streak Master",
      description: "12 days of continuous learning",
      earned_date: "2024-01-15",
      badge_type: "gold",
      icon: "🔥",
    },
    {
      title: "Quiz Champion",
      description: "Scored 90%+ on 10 quizzes",
      earned_date: "2024-01-12",
      badge_type: "silver",
      icon: "🏆",
    },
    {
      title: "Skill Builder",
      description: "Mastered 5 different skills",
      earned_date: "2024-01-08",
      badge_type: "gold",
      icon: "⭐",
    },
    {
      title: "Project Pioneer",
      description: "Completed first project",
      earned_date: "2024-01-05",
      badge_type: "bronze",
      icon: "🚀",
    },
  ],
  saved_content: [
    { id: "1", title: "React Best Practices Guide", type: "lesson", date_saved: "2024-01-14" },
    { id: "2", title: "Full Stack Developer Roadmap", type: "roadmap", date_saved: "2024-01-13" },
    { id: "3", title: "JavaScript Interview Questions", type: "resource", date_saved: "2024-01-12" },
    { id: "4", title: "API Design Patterns", type: "lesson", date_saved: "2024-01-11" },
  ],
  chat_history: [
    {
      id: "1",
      summary: "Discussion about React hooks and state management",
      date: "2024-01-15",
      topic: "React",
    },
    {
      id: "2",
      summary: "Career advice for transitioning to full-stack development",
      date: "2024-01-13",
      topic: "Career",
    },
    {
      id: "3",
      summary: "Help with debugging Node.js authentication issues",
      date: "2024-01-11",
      topic: "Node.js",
    },
    { id: "4", summary: "Best practices for database design", date: "2024-01-09", topic: "Database" },
  ],
  recommendations: {
    next_lessons: [
      {
        id: "1",
        title: "Advanced TypeScript Patterns",
        description: "Learn advanced TypeScript features for better code quality",
        estimated_time: "2.5 hours",
        difficulty: "intermediate",
        priority: 1,
      },
      {
        id: "2",
        title: "Testing with Jest and React Testing Library",
        description: "Master testing strategies for React applications",
        estimated_time: "3 hours",
        difficulty: "intermediate",
        priority: 2,
      },
      {
        id: "3",
        title: "GraphQL Fundamentals",
        description: "Learn modern API development with GraphQL",
        estimated_time: "4 hours",
        difficulty: "advanced",
        priority: 3,
      },
    ],
    career_opportunities: [
      {
        title: "Senior Frontend Developer",
        company: "TechCorp Inc",
        match_score: 89,
        salary_range: "$85k - $120k",
        location: "Remote",
        skills_required: ["React", "TypeScript", "Node.js"],
      },
      {
        title: "Full Stack Engineer",
        company: "StartupXYZ",
        match_score: 82,
        salary_range: "$90k - $130k",
        location: "San Francisco, CA",
        skills_required: ["React", "Node.js", "PostgreSQL", "AWS"],
      },
      {
        title: "React Developer",
        company: "WebAgency Pro",
        match_score: 95,
        salary_range: "$70k - $95k",
        location: "New York, NY",
        skills_required: ["React", "JavaScript", "CSS"],
      },
    ],
    skill_gaps: [
      { skill: "TypeScript", current_level: 2, target_level: 4, priority: "high", market_demand: "Very High" },
      { skill: "Testing", current_level: 1, target_level: 3, priority: "medium", market_demand: "High" },
      { skill: "DevOps", current_level: 0, target_level: 2, priority: "low", market_demand: "Medium" },
      {
        skill: "System Design",
        current_level: 1,
        target_level: 4,
        priority: "high",
        market_demand: "Very High",
      },
    ],
    market_trends: [
      {
        trend: "AI Integration in Web Development",
        description: "Growing demand for developers who can integrate AI/ML features",
        growth_rate: "+45%",
        relevance_score: 92,
      },
      {
        trend: "Serverless Architecture",
        description: "Increasing adoption of serverless technologies",
        growth_rate: "+38%",
        relevance_score: 85,
      },
      {
        trend: "Web3 and Blockchain",
        description: "Emerging opportunities in decentralized applications",
        growth_rate: "+67%",
        relevance_score: 78,
      },
    ],
    general_recommendations: [
      {
        id: "g1",
        title: "Explore new AI frameworks",
        description: "Stay updated with the latest in AI development.",
        link: "#",
      },
      {
        id: "g2",
        title: "Contribute to open source",
        description: "Enhance your portfolio and collaborate with others.",
        link: "#",
      },
    ],
  },
  analytics: {
    learning_timeline: [
      { date: "2024-01-08", lessons: 2, hours: 3.5, skills_gained: 1 },
      { date: "2024-01-09", lessons: 3, hours: 5.0, skills_gained: 2 },
      { date: "2024-01-10", lessons: 1, hours: 2.5, skills_gained: 0 },
    ],
    skill_levels: [
      { skill: "JavaScript", level: 4, max_level: 5, progress_percentage: 80 },
      { skill: "React", level: 4, max_level: 5, progress_percentage: 75 },
    ],
    time_distribution: [
      { activity: "Lessons", hours: 35, percentage: 52, color: "#3B82F6" },
      { activity: "Projects", hours: 18, percentage: 27, color: "#10B981" },
    ],
    career_progress: [
      { milestone: "Learn React Basics", completed: true, date: "2024-01-01", progress_percentage: 100 },
      { milestone: "Build First Project", completed: true, date: "2024-01-05", progress_percentage: 100 },
    ],
  },
  user_role: "student",
})

export default function DashboardPage() {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isRefreshing, setIsRefreshing] = useState(false)

  const session = useSession()

  const fetchDashboardData = useCallback(
    async (showRefreshToast = false) => {
      if (!session?.user?.id) {
        setDashboardData(generateMockData())
        setLoading(false)
        return
      }

      try {
        if (showRefreshToast) {
          setIsRefreshing(true)
        } else {
          setLoading(true)
        }
        setError(null)

        const [progressRes, recommendationsRes] = await Promise.allSettled([
          getUserProgress(session.user.id),
          getRecommendations(session.user.id, "student", []),
        ])

        const mockData = generateMockData()
        let combinedData: DashboardData = mockData

        if (progressRes.status === "fulfilled" && progressRes.value) {
          combinedData = {
            ...combinedData,
            progress: { ...combinedData.progress, ...progressRes.value.progress },
            recent_activity: progressRes.value.recent_activity || combinedData.recent_activity,
            achievements: progressRes.value.achievements || combinedData.achievements,
          }
        }

        if (recommendationsRes.status === "fulfilled" && recommendationsRes.value) {
          combinedData = {
            ...combinedData,
            recommendations: { ...combinedData.recommendations, ...recommendationsRes.value },
          }
        }

        setDashboardData(combinedData)

        if (showRefreshToast) {
          toast({
            title: "Dashboard Updated",
            description: "Your dashboard data has been refreshed successfully.",
          })
        }
      } catch (err) {
        console.error("Failed to fetch dashboard data:", err)
        setDashboardData(generateMockData())

        if (showRefreshToast) {
          toast({
            title: "Using Demo Data",
            description: "Showing demo data while backend services are connecting.",
          })
        }
      } finally {
        setLoading(false)
        setIsRefreshing(false)
      }
    },
    [session?.user?.id],
  )

  useEffect(() => {
    fetchDashboardData()
  }, [fetchDashboardData])

  const handleExportData = () => {
    if (!dashboardData) return

    const dataToExport = {
      progress: dashboardData.progress,
      analytics: dashboardData.analytics,
      exported_at: new Date().toISOString(),
    }

    const blob = new Blob([JSON.stringify(dataToExport, null, 2)], { type: "application/json" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `trainpi-progress-${new Date().toISOString().split("T")[0]}.json`
    a.click()
    URL.revokeObjectURL(url)

    toast({
      title: "Success",
      description: "Progress data exported successfully!",
    })
  }

  const handleRefresh = () => {
    fetchDashboardData(true)
  }

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <div className="h-8 bg-gray-200 rounded w-64 mb-2 animate-pulse"></div>
            <div className="h-4 bg-gray-200 rounded w-96 animate-pulse"></div>
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {[...Array(4)].map((_, i) => (
            <Card key={i} className="animate-pulse">
              <CardContent className="p-6">
                <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                <div className="h-8 bg-gray-200 rounded w-1/2 mb-2"></div>
                <div className="h-2 bg-gray-200 rounded w-full"></div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    )
  }

  if (!dashboardData) {
    return (
      <div className="container mx-auto px-4 py-8">
        <Card>
          <CardContent className="p-6 text-center">
            <p className="text-muted-foreground mb-4">Unable to load dashboard data</p>
            <Button onClick={handleRefresh} disabled={isRefreshing}>
              <RefreshCw className={`h-4 w-4 mr-2 ${isRefreshing ? "animate-spin" : ""}`} />
              {isRefreshing ? "Refreshing..." : "Try Again"}
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="flex-1 p-4 md:p-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon">
            <Settings className="h-5 w-5" />
            <span className="sr-only">Settings</span>
          </Button>
          <Button variant="ghost" size="icon">
            <LogOut className="h-5 w-5" />
            <span className="sr-only">Log out</span>
          </Button>
          <Avatar className="h-9 w-9">
            <AvatarImage src="/placeholder-user.jpg" />
            <AvatarFallback>JP</AvatarFallback>
          </Avatar>
        </div>
      </div>

      <Tabs defaultValue="overview" className="w-full">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="activity">Activity</TabsTrigger>
          <TabsTrigger value="achievements">Achievements</TabsTrigger>
          <TabsTrigger value="recommendations">Recommendations</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="mt-6">
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            <Suspense fallback={<div>Loading progress...</div>}>
              <ProgressOverview dashboardData={dashboardData} />
            </Suspense>
            <Card>
              <CardHeader>
                <CardTitle>Current Role</CardTitle>
                <CardDescription>Your current learning focus.</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold capitalize">{dashboardData.user_role}</div>
                <p className="text-sm text-muted-foreground">
                  {dashboardData.user_role === "student"
                    ? "Focusing on foundational knowledge and exploring new fields."
                    : "Advancing specialized skills and career growth."}
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Next Lesson</CardTitle>
                <CardDescription>Continue your learning journey.</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-lg font-medium">Introduction to Quantum Computing</div>
                <p className="text-sm text-muted-foreground">Module 3: Quantum Algorithms</p>
                <Button className="mt-4 w-full">Start Lesson</Button>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="activity" className="mt-6">
          <Suspense fallback={<div>Loading recent activity...</div>}>
            <RecentActivity dashboardData={dashboardData} />
          </Suspense>
        </TabsContent>

        <TabsContent value="achievements" className="mt-6">
          <Suspense fallback={<div>Loading achievements...</div>}>
            <Achievements dashboardData={dashboardData} />
          </Suspense>
        </TabsContent>

        <TabsContent value="recommendations" className="mt-6">
          <Suspense fallback={<div>Loading recommendations...</div>}>
            <Recommendations dashboardData={dashboardData} />
          </Suspense>
        </TabsContent>

        <TabsContent value="analytics" className="mt-6">
          <Suspense fallback={<div>Loading analytics...</div>}>
            <AnalyticsCharts dashboardData={dashboardData} />
          </Suspense>
        </TabsContent>
      </Tabs>
    </div>
  )
}
