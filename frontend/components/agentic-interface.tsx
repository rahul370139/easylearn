"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ScrollArea } from "@/components/ui/scroll-area"
import { useAuth } from "@/components/auth-provider"
import { learnAPI } from "@/lib/api"
import {
  Brain,
  Target,
  TrendingUp,
  BookOpen,
  CheckCircle,
  AlertCircle,
  Lightbulb,
  FileText,
  HelpCircle,
  Zap,
  BarChart3,
  Award,
} from "lucide-react"

interface MasteryData {
  user_id: string
  topics: Array<{
    topic: string
    mastery_level: number
    confidence: number
    last_assessed: string
  }>
  overall_progress: number
  strengths: string[]
  areas_for_improvement: string[]
  recommendations: string[]
}

interface AgentResponse {
  intent?: string
  response?: string
  content?: any
  summary?: string
  diagnostic?: any
  generated_content?: any
}

export function AgenticInterface() {
  const { user } = useAuth()
  const [masteryData, setMasteryData] = useState<MasteryData | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [currentResponse, setCurrentResponse] = useState<AgentResponse | null>(null)
  const [activeTab, setActiveTab] = useState("overview")

  // Quick action buttons for Agentic AI
  const quickActions = [
    {
      id: "summary",
      label: "Summary",
      icon: FileText,
      prompt: "Provide a summary of the uploaded content",
      description: "Get a concise overview",
    },
    {
      id: "lesson",
      label: "Lesson",
      icon: BookOpen,
      prompt: "Create a lesson plan from this content",
      description: "Generate structured learning",
    },
    {
      id: "diagnostic",
      label: "Diagnostic",
      icon: Target,
      prompt: "Run a diagnostic assessment",
      description: "Test your knowledge",
    },
    {
      id: "quiz",
      label: "Quiz",
      icon: HelpCircle,
      prompt: "Generate quiz questions",
      description: "Practice with questions",
    },
    {
      id: "flashcards",
      label: "Flashcards",
      icon: Zap,
      prompt: "Create flashcards for key concepts",
      description: "Quick review cards",
    },
    {
      id: "workflow",
      label: "Workflow",
      icon: BarChart3,
      prompt: "Create a learning workflow",
      description: "Step-by-step process",
    },
    {
      id: "progress",
      label: "Progress",
      icon: Award,
      prompt: "Show my learning progress",
      description: "Track achievements",
    },
  ]

  useEffect(() => {
    loadMasteryData()
  }, [user])

  const loadMasteryData = async () => {
    if (!user?.id) {
      // Set default data for anonymous users
      setMasteryData({
        user_id: "anonymous",
        topics: [],
        overall_progress: 0,
        strengths: [],
        areas_for_improvement: [],
        recommendations: ["Sign in to track your learning progress"],
      })
      return
    }

    try {
      setIsLoading(true)
      const data = await learnAPI.getMastery(user.id)
      setMasteryData(data)
    } catch (error) {
      console.error("Failed to load mastery data:", error)
      // Set fallback data
      setMasteryData({
        user_id: user.id,
        topics: [],
        overall_progress: 0,
        strengths: [],
        areas_for_improvement: [],
        recommendations: ["Unable to load progress data. Please try again later."],
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleQuickAction = async (action: (typeof quickActions)[0]) => {
    if (!user?.id) {
      alert("Please sign in to use AI features")
      return
    }

    setIsLoading(true)
    try {
      let response: AgentResponse = {}

      switch (action.id) {
        case "summary":
          response = await learnAPI.getSummary({
            content: action.prompt,
            user_id: user.id,
          })
          break
        case "diagnostic":
          response = await learnAPI.getDiagnostic({
            topic: "general",
            user_id: user.id,
          })
          break
        case "progress":
          await loadMasteryData()
          response = { response: "Progress data refreshed" }
          break
        default:
          response = await learnAPI.generateContent({
            type: action.id,
            topic: action.prompt,
            difficulty: "intermediate",
            user_id: user.id,
          })
      }

      setCurrentResponse(response)
      setActiveTab("results")
    } catch (error) {
      console.error(`Failed to execute ${action.id}:`, error)
      setCurrentResponse({
        response: `Failed to execute ${action.label}. Please try again.`,
      })
      setActiveTab("results")
    } finally {
      setIsLoading(false)
    }
  }

  const renderMasteryOverview = () => {
    if (!masteryData) return null

    return (
      <div className="space-y-6">
        {/* Overall Progress */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              Overall Progress
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Learning Progress</span>
                <span>{masteryData.overall_progress}%</span>
              </div>
              <Progress value={masteryData.overall_progress} className="h-2" />
            </div>
          </CardContent>
        </Card>

        {/* Topics Mastery */}
        {masteryData.topics.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Brain className="h-5 w-5" />
                Topic Mastery
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {masteryData.topics.map((topic, index) => (
                  <div key={index} className="space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="font-medium">{topic.topic}</span>
                      <Badge variant={topic.mastery_level > 70 ? "default" : "secondary"}>{topic.mastery_level}%</Badge>
                    </div>
                    <Progress value={topic.mastery_level} className="h-1" />
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Strengths & Areas for Improvement */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-green-600">
                <CheckCircle className="h-5 w-5" />
                Strengths
              </CardTitle>
            </CardHeader>
            <CardContent>
              {masteryData.strengths.length > 0 ? (
                <ul className="space-y-2">
                  {masteryData.strengths.map((strength, index) => (
                    <li key={index} className="flex items-center gap-2">
                      <div className="h-2 w-2 bg-green-500 rounded-full" />
                      {strength}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-muted-foreground">
                  {user?.id ? "Complete assessments to identify strengths" : "Sign in to track strengths"}
                </p>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-orange-600">
                <AlertCircle className="h-5 w-5" />
                Areas for Improvement
              </CardTitle>
            </CardHeader>
            <CardContent>
              {masteryData.areas_for_improvement.length > 0 ? (
                <ul className="space-y-2">
                  {masteryData.areas_for_improvement.map((area, index) => (
                    <li key={index} className="flex items-center gap-2">
                      <div className="h-2 w-2 bg-orange-500 rounded-full" />
                      {area}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-muted-foreground">
                  {user?.id ? "Great job! No major areas identified" : "Sign in to track improvement areas"}
                </p>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Recommendations */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Lightbulb className="h-5 w-5" />
              Recommendations
            </CardTitle>
          </CardHeader>
          <CardContent>
            {masteryData.recommendations.length > 0 ? (
              <ul className="space-y-2">
                {masteryData.recommendations.map((rec, index) => (
                  <li key={index} className="flex items-start gap-2">
                    <div className="h-2 w-2 bg-blue-500 rounded-full mt-2" />
                    {rec}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-muted-foreground">No specific recommendations at this time.</p>
            )}
          </CardContent>
        </Card>
      </div>
    )
  }

  const renderResults = () => {
    if (!currentResponse) {
      return (
        <div className="text-center py-8">
          <p className="text-muted-foreground">No results to display yet.</p>
          <p className="text-sm text-muted-foreground mt-2">Use the quick actions above to generate content.</p>
        </div>
      )
    }

    return (
      <Card>
        <CardHeader>
          <CardTitle>AI Response</CardTitle>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-96">
            <div className="space-y-4">
              {currentResponse.summary && (
                <div>
                  <h4 className="font-semibold mb-2">Summary</h4>
                  <p className="text-sm">{currentResponse.summary}</p>
                </div>
              )}

              {currentResponse.response && (
                <div>
                  <h4 className="font-semibold mb-2">Response</h4>
                  <p className="text-sm whitespace-pre-wrap">{currentResponse.response}</p>
                </div>
              )}

              {currentResponse.diagnostic && (
                <div>
                  <h4 className="font-semibold mb-2">Diagnostic Results</h4>
                  <pre className="text-sm bg-muted p-4 rounded overflow-auto">
                    {JSON.stringify(currentResponse.diagnostic, null, 2)}
                  </pre>
                </div>
              )}

              {currentResponse.generated_content && (
                <div>
                  <h4 className="font-semibold mb-2">Generated Content</h4>
                  <pre className="text-sm bg-muted p-4 rounded overflow-auto">
                    {JSON.stringify(currentResponse.generated_content, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center space-y-2">
        <h2 className="text-2xl font-bold">Agentic AI Learning Assistant</h2>
        <p className="text-muted-foreground">
          Personalized AI-powered learning with real-time diagnostics and progress tracking
        </p>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
            {quickActions.map((action) => {
              const Icon = action.icon
              return (
                <Button
                  key={action.id}
                  variant="outline"
                  className="h-auto p-4 flex flex-col items-center gap-2 bg-transparent"
                  onClick={() => handleQuickAction(action)}
                  disabled={isLoading}
                >
                  <Icon className="h-6 w-6" />
                  <span className="text-xs font-medium">{action.label}</span>
                </Button>
              )
            })}
          </div>
        </CardContent>
      </Card>

      {/* Main Content Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="diagnostic">Diagnostic</TabsTrigger>
          <TabsTrigger value="results">Results</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          {isLoading ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
              <p className="mt-2 text-muted-foreground">Loading mastery data...</p>
            </div>
          ) : (
            renderMasteryOverview()
          )}
        </TabsContent>

        <TabsContent value="diagnostic" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Target className="h-5 w-5" />
                Learning Diagnostic
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8">
                <p className="text-muted-foreground mb-4">
                  Run a diagnostic assessment to identify your current knowledge level and areas for improvement.
                </p>
                <Button
                  onClick={() => handleQuickAction(quickActions.find((a) => a.id === "diagnostic")!)}
                  disabled={isLoading}
                >
                  <Target className="mr-2 h-4 w-4" />
                  Start Diagnostic
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="results" className="space-y-6">
          {renderResults()}
        </TabsContent>
      </Tabs>
    </div>
  )
}
