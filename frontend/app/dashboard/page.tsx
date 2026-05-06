"use client"

import Link from "next/link"
import { useState, useEffect, useCallback } from "react"
import { dashboardAPI, userAPI, recommendationAPI, learnAPI, careerAPI } from "@/lib/api"
import { useAuth } from "@/components/auth-provider"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { ProgressOverview } from "@/components/dashboard/progress-overview"
import { RecentActivity } from "@/components/dashboard/recent-activity"
import { Achievements } from "@/components/dashboard/achievements"
import { Recommendations } from "@/components/dashboard/recommendations"
import { AnalyticsCharts } from "@/components/dashboard/analytics-charts"
import { RefreshCw, LogIn } from "lucide-react"
import { toast } from "@/components/ui/use-toast"
import type { DashboardData } from "@/types/dashboard"
import { Suspense } from "react"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"

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

// Mock data generator function — matches the DashboardData type so guests
// see a populated layout while we wait for them to sign in.
const generateMockData = (): DashboardData => ({
  progress: {
    completed_lessons: 24,
    total_lessons: 100,
    progress_percentage: 24,
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
  const [_, setError] = useState<string | null>(null)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [lastRefreshedAt, setLastRefreshedAt] = useState<string | null>(null)
  const [savedCareerPlan, setSavedCareerPlan] = useState<{
    saved_at?: string
    target_role?: string
  } | null>(null)

  // Single source of auth truth. The previous `useSession()` from
  // @supabase/auth-helpers-react silently returned null because the app
  // doesn't mount a SessionContextProvider — that's why every signed-in user
  // saw mock data on this page.
  const { user, loading: authLoading, signOut } = useAuth()

  const fetchDashboardData = useCallback(
    async (showRefreshToast = false) => {
      if (!user?.id) {
        // Guest view: show the demo dataset so the page is still useful.
        setDashboardData(generateMockData())
        setLoading(false)
        setLastRefreshedAt(new Date().toISOString())
        setSavedCareerPlan(null)
        return
      }

      try {
        if (showRefreshToast) {
          setIsRefreshing(true)
        } else {
          setLoading(true)
        }
        setError(null)

        const [progressRes, recommendationsRes, careerSnapRes] = await Promise.allSettled([
          getUserProgress(user.id),
          getRecommendations(user.id, "student", []),
          careerAPI.getLatestCareerPlan(user.id),
        ])

        // Use mock data only as a structural skeleton; we overwrite every
        // section we successfully fetch from the backend.
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

        if (careerSnapRes.status === "fulfilled" && careerSnapRes.value?.has_plan && careerSnapRes.value.plan) {
          const snap = careerSnapRes.value.plan as { target_role?: string }
          setSavedCareerPlan({
            saved_at: careerSnapRes.value.saved_at,
            target_role: snap.target_role,
          })
        } else {
          setSavedCareerPlan(null)
        }

        if (showRefreshToast) {
          toast({
            title: "Dashboard updated",
            description: "Your data has been refreshed.",
          })
        }
      } catch (err) {
        console.error("Failed to fetch dashboard data:", err)
        setDashboardData(generateMockData())

        if (showRefreshToast) {
          toast({
            title: "Using demo data",
            description: "Backend reachable failed; showing the demo dataset.",
          })
        }
      } finally {
        setLoading(false)
        setIsRefreshing(false)
        if (user?.id) {
          setLastRefreshedAt(new Date().toISOString())
        }
      }
    },
    [user?.id],
  )

  useEffect(() => {
    if (authLoading) return
    fetchDashboardData()
  }, [authLoading, fetchDashboardData])

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

  const isSignedIn = !!user?.id
  const displayName =
    (user?.user_metadata?.full_name as string | undefined) ||
    (user?.user_metadata?.name as string | undefined) ||
    (user?.email ? user.email.split("@")[0] : "")
  const avatarUrl =
    (user?.user_metadata?.avatar_url as string | undefined) ||
    (user?.user_metadata?.picture as string | undefined) ||
    "/placeholder-user.jpg"
  const initials = (displayName || user?.email || "G").slice(0, 2).toUpperCase()

  return (
    <div className="flex-1 p-4 md:p-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold">Dashboard</h1>
          <p className="text-sm text-muted-foreground">
            {isSignedIn
              ? `Welcome back${displayName ? `, ${displayName}` : ""}.`
              : "You're viewing the demo dashboard."}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            disabled={isRefreshing || !isSignedIn}
            title={isSignedIn ? "Refresh your data" : "Sign in to refresh real data"}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${isRefreshing ? "animate-spin" : ""}`} />
            {isRefreshing ? "Refreshing…" : "Refresh"}
          </Button>
          {isSignedIn ? (
            <Button variant="ghost" size="sm" onClick={() => void signOut()}>
              Sign out
            </Button>
          ) : (
            <Button asChild size="sm">
              <Link href="/login">
                <LogIn className="h-4 w-4 mr-2" />
                Sign in
              </Link>
            </Button>
          )}
          <Avatar className="h-9 w-9">
            <AvatarImage src={avatarUrl} />
            <AvatarFallback className="bg-gradient-to-r from-blue-500 to-purple-500 text-white">
              {initials}
            </AvatarFallback>
          </Avatar>
        </div>
      </div>

      {!isSignedIn && (
        <Card className="mb-6 border-dashed border-blue-300 bg-blue-50/50 dark:bg-blue-950/20">
          <CardContent className="p-4 flex flex-col md:flex-row md:items-center md:justify-between gap-3">
            <div className="space-y-1">
              <p className="text-sm font-medium">You're seeing demo numbers.</p>
              <p className="text-xs text-muted-foreground">
                Sign in to track real progress, save your career roadmap, and see personalised recommendations.
              </p>
            </div>
            <Button asChild>
              <Link href="/login">Sign in to personalise</Link>
            </Button>
          </CardContent>
        </Card>
      )}

      {isSignedIn && (
        <div className="mb-6 space-y-3">
          <div className="flex flex-wrap items-center gap-2 text-xs">
            <Badge variant="outline" className="bg-green-50 text-green-700 border-green-300 dark:bg-green-950/20 dark:text-green-300">
              ● Live data for {user.email}
            </Badge>
            {lastRefreshedAt && (
              <span className="text-muted-foreground">
                Last refreshed{" "}
                {new Date(lastRefreshedAt).toLocaleString(undefined, {
                  dateStyle: "medium",
                  timeStyle: "short",
                })}
              </span>
            )}
          </div>
          {savedCareerPlan?.target_role && (
            <Card className="border-violet-200/80 bg-violet-50/40 dark:bg-violet-950/15 dark:border-violet-900">
              <CardContent className="p-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                <div>
                  <p className="text-sm font-medium">Saved career upgrade plan</p>
                  <p className="text-xs text-muted-foreground">
                    Target: <span className="font-semibold text-foreground">{savedCareerPlan.target_role}</span>
                    {savedCareerPlan.saved_at
                      ? ` · Saved ${new Date(savedCareerPlan.saved_at).toLocaleDateString(undefined, {
                          dateStyle: "medium",
                        })}`
                      : ""}
                  </p>
                </div>
                <Button asChild size="sm" variant="secondary">
                  <Link href="/career">Review on Career page</Link>
                </Button>
              </CardContent>
            </Card>
          )}
        </div>
      )}

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
