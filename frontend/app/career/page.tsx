"use client"

import { useState } from "react"
import { careerAPI } from "@/lib/api"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Progress } from "@/components/ui/progress"
import { ResumeCareerUpgrade } from "@/components/resume-career-upgrade"
import {
  Code,
  Briefcase,
  TrendingUp,
  ArrowRight,
  ArrowLeft,
  HelpCircle,
  Brain,
  Download,
  Share,
  Clock,
  Award,
  Target,
  Sparkles,
} from "lucide-react"
import { useAuth } from "@/components/auth-provider"

const assessmentQuestions = [
  { id: 1, question: "I enjoy working with technology and solving technical problems", type: "likert" },
  { id: 2, question: "I prefer working independently rather than in large teams", type: "likert" },
  { id: 3, question: "I like analyzing data to find patterns and insights", type: "likert" },
  { id: 4, question: "I enjoy creating visual designs and user interfaces", type: "likert" },
  { id: 5, question: "I'm comfortable presenting ideas to groups of people", type: "likert" },
  { id: 6, question: "I prefer structured, predictable work environments", type: "likert" },
  { id: 7, question: "I enjoy mentoring and helping others learn", type: "likert" },
  { id: 8, question: "I like working on long-term strategic projects", type: "likert" },
  { id: 9, question: "I'm energized by fast-paced, changing environments", type: "likert" },
  { id: 10, question: "I enjoy learning new technologies and staying updated with industry trends", type: "likert" },
]

const likertOptions = [
  { value: "1", label: "Strongly Disagree" },
  { value: "2", label: "Disagree" },
  { value: "3", label: "Neutral" },
  { value: "4", label: "Agree" },
  { value: "5", label: "Strongly Agree" },
]

export default function CareerPage() {
  const { user } = useAuth()

  const [showAssessment, setShowAssessment] = useState(false)
  const [currentStep, setCurrentStep] = useState(0)
  const [answers, setAnswers] = useState<Record<number, string>>({})
  const [showResults, setShowResults] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [careerResults, setCareerResults] = useState<any[]>([])

  const [roadmapData, setRoadmapData] = useState<any>(null)
  const [showRoadmap, setShowRoadmap] = useState(false)
  const [roadmapTargetRole, setRoadmapTargetRole] = useState("")

  const handleAnswerChange = (questionId: number, value: string) => {
    setAnswers((prev) => ({ ...prev, [questionId]: value }))
  }

  const handleNext = async () => {
    if (currentStep < assessmentQuestions.length - 1) {
      setCurrentStep((prev) => prev + 1)
      return
    }
    setIsLoading(true)
    try {
      const answersArray = Object.entries(answers).map(([question_id, rating]) => ({
        question_id: Number.parseInt(question_id),
        rating: Number.parseInt(rating),
      }))
      const timeoutPromise = new Promise((_, reject) =>
        setTimeout(() => reject(new Error("Request timeout")), 30000),
      )
      const result: any = await Promise.race([
        careerAPI.matchCareer({ user_id: user?.id || "anonymous-user", answers: answersArray }),
        timeoutPromise,
      ])
      setCareerResults(result.career_matches || result.results || [])
      setShowResults(true)
    } catch (error) {
      console.error("Career matching failed:", error)
      setCareerResults([])
      setShowResults(true)
    } finally {
      setIsLoading(false)
    }
  }

  const handlePrevious = () => setCurrentStep((prev) => prev - 1)

  const handleGenerateRoadmapFromQuiz = async (careerTitle: string) => {
    setIsLoading(true)
    setRoadmapTargetRole(careerTitle)
    try {
      const data = await careerAPI.generateRoadmap({
        target_role: careerTitle,
        interests: ["technology", "problem-solving"],
        skills: [],
        user_id: user?.id || "anonymous-user",
      })
      setRoadmapData(data)
      setShowRoadmap(true)
      setShowResults(false)
    } catch (error) {
      console.error("Failed to generate roadmap from quiz:", error)
    } finally {
      setIsLoading(false)
    }
  }

  // ----- Loading splash -----
  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-2xl mx-auto text-center space-y-6">
          <div className="w-16 h-16 mx-auto bg-gradient-to-r from-blue-500 to-purple-500 rounded-full flex items-center justify-center">
            <Brain className="h-8 w-8 text-white animate-spin" />
          </div>
          <h2 className="text-2xl font-bold">Crunching the numbers…</h2>
          <p className="text-muted-foreground">Matching your responses against O*NET career data.</p>
          <div className="flex justify-center space-x-2">
            <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" />
            <div className="w-2 h-2 bg-purple-500 rounded-full animate-bounce" style={{ animationDelay: "0.1s" }} />
            <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: "0.2s" }} />
          </div>
        </div>
      </div>
    )
  }

  // ----- Quiz results -----
  if (showResults) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto space-y-8">
          <div className="text-center space-y-4">
            <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              Your Career Matches
            </h1>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              Based on your responses, here are the careers that align best with your interests.
            </p>
          </div>

          {careerResults.length === 0 ? (
            <Card>
              <CardContent className="p-6 text-center text-sm text-muted-foreground">
                We couldn't reach the career matcher. Try again in a moment, or upload your resume below for a
                concrete upgrade plan instead.
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-6">
              {careerResults.map((career, index) => (
                <Card key={index} className="group hover:shadow-lg transition-all duration-300 border-0 shadow-md">
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-4">
                        <div className="p-3 rounded-lg bg-gradient-to-r from-blue-500 to-purple-500 text-white">
                          <Briefcase className="h-6 w-6" />
                        </div>
                        <div className="space-y-1">
                          <CardTitle className="text-xl group-hover:text-primary transition-colors">
                            {career.career || career.title}
                          </CardTitle>
                          <CardDescription className="text-sm">{career.description}</CardDescription>
                          <p className="text-sm font-medium text-green-600 dark:text-green-400">
                            ${career.salary_low?.toLocaleString() || "50,000"} – $
                            {career.salary_high?.toLocaleString() || "100,000"}
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <Badge variant="secondary" className="text-lg font-bold bg-gradient-to-r from-blue-500 to-purple-500 text-white">
                          {Math.round((career.match_score || career.similarity || 0) * 100)}%
                        </Badge>
                        <p className="text-xs text-muted-foreground mt-1">Match</p>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div>
                        <p className="text-sm font-medium mb-2">Key skills</p>
                        <div className="flex flex-wrap gap-2">
                          {(career.top_skills ? career.top_skills.split(",").slice(0, 4) : career.skills || []).map(
                            (skill: string, skillIndex: number) => (
                              <Badge key={skillIndex} variant="outline" className="text-xs">
                                {skill.trim()}
                              </Badge>
                            ),
                          )}
                        </div>
                      </div>
                      <Button
                        onClick={() => handleGenerateRoadmapFromQuiz(career.career || career.title)}
                        className="w-full bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600"
                      >
                        Generate learning roadmap
                        <ArrowRight className="ml-2 h-4 w-4" />
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}

          <div className="text-center">
            <Button
              variant="outline"
              onClick={() => {
                setShowResults(false)
                setShowAssessment(false)
                setCurrentStep(0)
                setAnswers({})
              }}
              className="mr-4 bg-transparent"
            >
              Back to career tools
            </Button>
          </div>
        </div>
      </div>
    )
  }

  // ----- Roadmap from quiz -----
  if (showRoadmap && roadmapData) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto space-y-8">
          <div className="text-center space-y-4">
            <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              {roadmapData.career_title || roadmapTargetRole} learning roadmap
            </h1>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              A personalised journey toward {roadmapData.career_title || roadmapTargetRole}.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <Card className="text-center">
              <CardContent className="p-6">
                <Clock className="h-8 w-8 mx-auto mb-2 text-blue-500" />
                <p className="text-2xl font-bold text-primary">
                  {roadmapData.estimated_time_to_target?.estimated_years
                    ? `${roadmapData.estimated_time_to_target.estimated_years} years`
                    : "6-12 months"}
                </p>
                <p className="text-sm text-muted-foreground">Total duration</p>
              </CardContent>
            </Card>
            <Card className="text-center">
              <CardContent className="p-6">
                <Award className="h-8 w-8 mx-auto mb-2 text-purple-500" />
                <p className="text-2xl font-bold text-primary">
                  {roadmapData.confidence_score ? `${Math.round(roadmapData.confidence_score * 100)}%` : "85%"}
                </p>
                <p className="text-sm text-muted-foreground">Confidence</p>
              </CardContent>
            </Card>
            <Card className="text-center">
              <CardContent className="p-6">
                <Target className="h-8 w-8 mx-auto mb-2 text-green-500" />
                <p className="text-2xl font-bold text-primary">
                  {roadmapData.roadmap ? Object.keys(roadmapData.roadmap).length : 3}
                </p>
                <p className="text-sm text-muted-foreground">Career levels</p>
              </CardContent>
            </Card>
            <Card className="text-center">
              <CardContent className="p-6">
                <TrendingUp className="h-8 w-8 mx-auto mb-2 text-orange-500" />
                <p className="text-2xl font-bold text-primary">
                  {roadmapData.market_insights?.growth_rate || "15%"}
                </p>
                <p className="text-sm text-muted-foreground">Growth rate</p>
              </CardContent>
            </Card>
          </div>

          <div className="flex justify-center gap-4">
            <Button className="bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600">
              <Download className="mr-2 h-4 w-4" />
              Download roadmap
            </Button>
            <Button variant="outline">
              <Share className="mr-2 h-4 w-4" />
              Share
            </Button>
          </div>

          {roadmapData.roadmap && (
            <div className="space-y-6">
              <h2 className="text-2xl font-bold text-center">Career progression</h2>
              <div className="grid gap-6 md:grid-cols-3">
                {Object.entries(roadmapData.roadmap).map(([level, details]: [string, any]) => {
                  if (level === "skill_gaps" || level === "metadata") return null
                  return (
                    <Card key={level} className="hover:shadow-lg transition-shadow">
                      <CardHeader>
                        <CardTitle className="text-lg">{details.title}</CardTitle>
                        <div className="flex justify-between items-center text-sm text-muted-foreground">
                          <span>{details.duration}</span>
                          <span className="font-medium text-green-600">{details.salary_range}</span>
                        </div>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <div>
                          <h4 className="font-medium mb-2">Key skills</h4>
                          <div className="flex flex-wrap gap-1">
                            {details.skills?.slice(0, 4).map((skill: string, idx: number) => (
                              <Badge key={idx} variant="secondary" className="text-xs">
                                {skill}
                              </Badge>
                            ))}
                          </div>
                        </div>
                        <div>
                          <h4 className="font-medium mb-2">Responsibilities</h4>
                          <ul className="text-sm text-muted-foreground space-y-1">
                            {details.responsibilities?.slice(0, 3).map((resp: string, idx: number) => (
                              <li key={idx} className="flex items-start">
                                <span className="mr-2">•</span>
                                <span>{resp}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      </CardContent>
                    </Card>
                  )
                })}
              </div>
            </div>
          )}

          <div className="text-center">
            <Button
              variant="outline"
              onClick={() => {
                setShowRoadmap(false)
                setRoadmapData(null)
              }}
              className="bg-transparent"
            >
              Back to career tools
            </Button>
          </div>
        </div>
      </div>
    )
  }

  // ----- Quiz form -----
  if (showAssessment) {
    const currentQuestion = assessmentQuestions[currentStep]
    const canGoNext = answers[currentQuestion?.id] !== undefined
    const progress = ((currentStep + 1) / assessmentQuestions.length) * 100

    return (
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-2xl mx-auto space-y-8">
          <div className="text-center space-y-4">
            <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              Career assessment
            </h1>
            <p className="text-muted-foreground">
              Question {currentStep + 1} of {assessmentQuestions.length}
            </p>
            <Progress value={progress} className="w-full" />
          </div>

          <Card className="border-0 shadow-lg">
            <CardHeader>
              <CardTitle className="text-xl">Question {currentStep + 1}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <p className="text-lg leading-relaxed">{currentQuestion.question}</p>
              <RadioGroup
                value={answers[currentQuestion.id] || ""}
                onValueChange={(value) => handleAnswerChange(currentQuestion.id, value)}
                className="space-y-3"
              >
                {likertOptions.map((option) => (
                  <div
                    key={option.value}
                    className="flex items-center space-x-3 p-3 rounded-lg hover:bg-accent transition-colors"
                  >
                    <RadioGroupItem value={option.value} id={`${currentQuestion.id}-${option.value}`} />
                    <Label htmlFor={`${currentQuestion.id}-${option.value}`} className="flex-1 cursor-pointer text-sm">
                      {option.label}
                    </Label>
                  </div>
                ))}
              </RadioGroup>
            </CardContent>
          </Card>

          <div className="flex justify-between">
            <Button
              variant="outline"
              onClick={handlePrevious}
              disabled={currentStep === 0}
              className="flex items-center gap-2 bg-transparent"
            >
              <ArrowLeft className="h-4 w-4" />
              Previous
            </Button>
            <Button
              onClick={handleNext}
              disabled={!canGoNext}
              className="flex items-center gap-2 bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600"
            >
              {currentStep === assessmentQuestions.length - 1 ? "Get results" : "Next"}
              <ArrowRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    )
  }

  // ----- Default landing: resume-driven upgrade in one panel -----
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="space-y-8">
        <div className="text-center space-y-4">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            Career upgrade
          </h1>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            Upload your resume, set a target, and get a concrete plan grounded in O*NET / BLS data.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Single tab — resume + target + interests in one flow */}
          <div className="lg:col-span-3">
            <ResumeCareerUpgrade />
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            <Card className="border-0 shadow-lg bg-gradient-to-br from-blue-50 to-purple-50 dark:from-blue-950/20 dark:to-purple-950/20">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-lg">
                  <HelpCircle className="h-5 w-5" />
                  No clue yet?
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-sm text-muted-foreground">
                  Not sure which path to chase? Take a 10-question quiz to surface careers that match your
                  preferences, then come back here to upload your resume.
                </p>
                <Button
                  onClick={() => setShowAssessment(true)}
                  className="w-full bg-gradient-to-r from-orange-500 to-red-500 hover:from-orange-600 hover:to-red-600"
                >
                  <Brain className="mr-2 h-4 w-4" />
                  Take the quiz
                </Button>
              </CardContent>
            </Card>

            <Card className="border-0 shadow-lg">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-lg">
                  <Sparkles className="h-5 w-5" />
                  How this works
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm text-muted-foreground">
                <p>
                  <span className="font-medium text-foreground">1. Upload</span> a PDF resume — we parse skills,
                  roles, and projects.
                </p>
                <p>
                  <span className="font-medium text-foreground">2. Pick</span> a target role and the interests
                  you want to lean into.
                </p>
                <p>
                  <span className="font-medium text-foreground">3. Get</span> a skill-gap analysis, 3-stage
                  roadmap, 90-day plan, projects, and interview prep — all anchored to O*NET data.
                </p>
              </CardContent>
            </Card>

            {!user && (
              <Card className="border-2 border-dashed">
                <CardHeader>
                  <CardTitle className="text-base flex items-center gap-2">
                    <Code className="h-4 w-4" />
                    Sign in to save plans
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-xs text-muted-foreground mb-3">
                    You can use everything as a guest, but signing in lets us save your roadmap and surface it
                    on the dashboard.
                  </p>
                  <Button asChild size="sm" variant="outline" className="w-full">
                    <a href="/login">Sign in</a>
                  </Button>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
