"use client"

import { useState } from "react"
import { careerAPI } from "@/lib/api"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Label } from "@/components/ui/label"
import { CareerStepper } from "@/components/career-stepper"
import { Skeleton } from "@/components/ui/skeleton"
import { useAuth } from "@/components/auth-provider"
import { RoadmapTimeline } from "@/components/roadmap-timeline"
import { Download, Share, Clock, Award, Target } from "lucide-react"

const questions = [
  {
    id: 1,
    question: "I enjoy working with technology and solving technical problems",
    type: "likert",
  },
  {
    id: 2,
    question: "I prefer working independently rather than in large teams",
    type: "likert",
  },
  {
    id: 3,
    question: "I like analyzing data to find patterns and insights",
    type: "likert",
  },
  {
    id: 4,
    question: "I enjoy creating visual designs and user interfaces",
    type: "likert",
  },
  {
    id: 5,
    question: "I'm comfortable presenting ideas to groups of people",
    type: "likert",
  },
  {
    id: 6,
    question: "I prefer structured, predictable work environments",
    type: "likert",
  },
  {
    id: 7,
    question: "I enjoy mentoring and helping others learn",
    type: "likert",
  },
  {
    id: 8,
    question: "I like working on long-term strategic projects",
    type: "likert",
  },
  {
    id: 9,
    question: "I'm energized by fast-paced, changing environments",
    type: "likert",
  },
  {
    id: 10,
    question: "I prefer hands-on, practical work over theoretical concepts",
    type: "likert",
  },
]

const likertOptions = [
  { value: "1", label: "Strongly Disagree" },
  { value: "2", label: "Disagree" },
  { value: "3", label: "Neutral" },
  { value: "4", label: "Agree" },
  { value: "5", label: "Strongly Agree" },
]

interface Career {
  career: string
  description: string
  match_score: number
}

export default function CareerDiscoverPage() {
  const [currentStep, setCurrentStep] = useState(1)
  const [answers, setAnswers] = useState<Record<number, string>>({})
  const [careers, setCareers] = useState<Career[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [showResults, setShowResults] = useState(false)
  const [roadmapData, setRoadmapData] = useState<any>(null)
  const [showRoadmap, setShowRoadmap] = useState(false)
  const { user } = useAuth()

  const handleAnswerChange = (questionId: number, value: string) => {
    setAnswers((prev) => ({ ...prev, [questionId]: value }))
  }

  const handleNext = async () => {
    if (currentStep === questions.length) {
      if (!user?.id) {
        alert("Please sign in to get your career matches")
        return
      }

      // Submit and get results
      setIsLoading(true)
      try {
        const data = await careerAPI.matchCareer({
          user_id: user.id,
          answers: Object.entries(answers).map(([question_id, rating]) => ({
            question_id: Number.parseInt(question_id),
            rating: Number.parseInt(rating),
          })),
        })

        setCareers(data.career_matches || data.results || [])
        setShowResults(true)
      } catch (error) {
        console.error("Failed to get career matches:", error)
        alert("Failed to get career matches. Please try again.")
      } finally {
        setIsLoading(false)
      }
    } else {
      setCurrentStep((prev) => prev + 1)
    }
  }

  const handlePrevious = () => {
    setCurrentStep((prev) => prev - 1)
  }

  const handleViewProfile = (careerId: string) => {
    // Navigate to career profile or show modal
    console.log("View profile for career:", careerId)
  }

  const handleGenerateRoadmap = async (careerTitle: string) => {
    setIsLoading(true)
    try {
      const data = await careerAPI.generateRoadmap({
        target_role: careerTitle,
        interests: ["technology", "problem-solving"], // Default interests from quiz
        skills: [], // Will be determined by the backend based on career
        user_id: user?.id || "anonymous-user",
      })

      console.log("Roadmap generated from quiz:", data)
      setRoadmapData(data)
      setShowRoadmap(true)
      setShowResults(false) // Hide quiz results, show roadmap
    } catch (error) {
      console.error("Failed to generate roadmap from quiz:", error)
      alert("Failed to generate roadmap. Please try again.")
    } finally {
      setIsLoading(false)
    }
  }

  const canGoNext = answers[currentStep] !== undefined

  if (isLoading) {
    return (
      <div className="space-y-8">
        <div className="text-center">
          <h1 className="text-3xl font-bold">Analyzing Your Responses...</h1>
          <p className="text-muted-foreground">Finding the best career matches for you</p>
        </div>
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {[...Array(5)].map((_, i) => (
            <Skeleton key={i} className="h-64 w-full rounded-lg" />
          ))}
        </div>
      </div>
    )
  }

  if (showResults) {
    return (
      <div className="space-y-8">
        <div className="text-center space-y-4">
          <h1 className="text-3xl font-bold">Your Career Matches</h1>
          <p className="text-muted-foreground">
            Based on your responses, here are the careers that align with your interests and preferences.
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {careers.map((career, index) => (
            <Card key={index} className="group hover:shadow-lg transition-all duration-300 hover:-translate-y-1">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">💼</span>
                    <div className="flex-1">
                      <CardTitle className="text-lg group-hover:text-primary transition-colors">
                        {career.career || career.title}
                      </CardTitle>
                      <p className="text-sm text-muted-foreground mt-1">
                        {career.day_in_life || career.description}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="text-sm font-medium text-primary">
                      {Math.round((career.match_score || career.similarity || 0) * 100)}%
                    </span>
                    <p className="text-xs text-muted-foreground">Match</p>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Salary and Growth Info */}
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-muted-foreground">Salary Range</p>
                    <p className="font-medium text-green-600">
                      ${career.salary_low?.toLocaleString() || '50,000'} - ${career.salary_high?.toLocaleString() || '100,000'}
                    </p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Growth Rate</p>
                    <p className="font-medium text-blue-600">
                      {career.growth_pct || 15}%
                    </p>
                  </div>
                </div>

                {/* Skills */}
                {career.common_skills && career.common_skills.length > 0 && (
                  <div>
                    <p className="text-sm font-medium mb-2">Key Skills:</p>
                    <div className="flex flex-wrap gap-1">
                      {career.common_skills.slice(0, 3).map((skill: string, skillIdx: number) => (
                        <Badge key={skillIdx} variant="outline" className="text-xs">
                          {skill}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}

                <div className="space-y-2">
                  <Button className="w-full" onClick={() => handleViewProfile(career.career || career.title)}>
                    View Career Profile
                  </Button>
                  <Button
                    variant="outline"
                    className="w-full bg-transparent"
                    onClick={() => handleGenerateRoadmap(career.career || career.title)}
                  >
                    Generate Roadmap
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="text-center">
          <Button
            variant="outline"
            onClick={() => {
              setShowResults(false)
              setCurrentStep(1)
              setAnswers({})
              setCareers([])
            }}
          >
            Take Assessment Again
          </Button>
        </div>
      </div>
    )
  }

  // Roadmap Display Screen
  if (showRoadmap && roadmapData) {
    return (
      <div className="max-w-4xl mx-auto space-y-8">
        <div className="text-center space-y-4">
          <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            {roadmapData.career_title || "Career"} Learning Roadmap
          </h1>
          <p className="text-muted-foreground max-w-2xl mx-auto">
            Your personalized learning journey to become a {roadmapData.career_title || "professional"}
          </p>
        </div>

        {/* Roadmap Overview */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card className="text-center">
            <CardContent className="p-6">
              <Clock className="h-8 w-8 mx-auto mb-2 text-blue-500" />
              <p className="text-2xl font-bold text-primary">{roadmapData.total_duration || "6-12 months"}</p>
              <p className="text-sm text-muted-foreground">Total Duration</p>
            </CardContent>
          </Card>
          <Card className="text-center">
            <CardContent className="p-6">
              <Award className="h-8 w-8 mx-auto mb-2 text-purple-500" />
              <p className="text-2xl font-bold text-primary capitalize">
                {roadmapData.difficulty_level || "Intermediate"}
              </p>
              <p className="text-sm text-muted-foreground">Difficulty Level</p>
            </CardContent>
          </Card>
          <Card className="text-center">
            <CardContent className="p-6">
              <Target className="h-8 w-8 mx-auto mb-2 text-green-500" />
              <p className="text-2xl font-bold text-primary">{roadmapData.steps?.length || 8}</p>
              <p className="text-sm text-muted-foreground">Learning Steps</p>
            </CardContent>
          </Card>
        </div>

        {/* Action Buttons */}
        <div className="flex justify-center gap-4">
          <Button className="bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600">
            <Download className="mr-2 h-4 w-4" />
            Download Roadmap
          </Button>
          <Button variant="outline">
            <Share className="mr-2 h-4 w-4" />
            Share Roadmap
          </Button>
        </div>

        {/* Roadmap Timeline */}
        {roadmapData.steps && (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold text-center">Your Learning Path</h2>
            <RoadmapTimeline steps={roadmapData.steps} />
          </div>
        )}

        {/* Back Button */}
        <div className="text-center">
          <Button
            variant="outline"
            onClick={() => {
              setShowRoadmap(false)
              setRoadmapData(null)
              setShowResults(true)
            }}
            className="bg-transparent"
          >
            Back to Career Matches
          </Button>
        </div>
      </div>
    )
  }

  const currentQuestion = questions[currentStep - 1]

  return (
    <div className="max-w-2xl mx-auto space-y-8">
      <div className="text-center space-y-4">
        <h1 className="text-3xl font-bold">Career Pathfinder</h1>
        <p className="text-muted-foreground">
          Answer these questions to discover careers that match your interests and work style.
        </p>
      </div>

      <CareerStepper
        currentStep={currentStep}
        totalSteps={questions.length}
        onNext={handleNext}
        onPrevious={handlePrevious}
        canGoNext={canGoNext}
      />

      <Card>
        <CardHeader>
          <CardTitle>Question {currentStep}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <p className="text-lg">{currentQuestion.question}</p>

          <RadioGroup
            value={answers[currentStep] || ""}
            onValueChange={(value) => handleAnswerChange(currentStep, value)}
          >
            {likertOptions.map((option) => (
              <div key={option.value} className="flex items-center space-x-2">
                <RadioGroupItem value={option.value} id={option.value} />
                <Label htmlFor={option.value} className="flex-1 cursor-pointer">
                  {option.label}
                </Label>
              </div>
            ))}
          </RadioGroup>
        </CardContent>
      </Card>
    </div>
  )
}
