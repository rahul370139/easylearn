"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Separator } from "@/components/ui/separator"
import { Loader2, Lightbulb, TrendingUp, AlertTriangle } from "lucide-react"
import {
  ChevronLeft,
  ChevronRight,
  RotateCcw,
  CheckCircle,
  XCircle,
  FileText,
  BookOpen,
  Brain,
  Workflow,
  Target,
  Download,
  Share,
  Copy,
  Eye,
  EyeOff,
} from "lucide-react"
import { agenticAPI } from "@/lib/api"

// Flashcards Component
interface FlashcardData {
  front: string
  back: string
}

interface FlashcardsComponentProps {
  flashcards: FlashcardData[]
  onAction?: (action: string) => void
}

export function FlashcardsComponent({ flashcards, onAction }: FlashcardsComponentProps) {
  const [currentIndex, setCurrentIndex] = useState(0)
  const [isFlipped, setIsFlipped] = useState(false)

  const nextCard = () => {
    setCurrentIndex((prev) => (prev + 1) % flashcards.length)
    setIsFlipped(false)
  }

  const prevCard = () => {
    setCurrentIndex((prev) => (prev - 1 + flashcards.length) % flashcards.length)
    setIsFlipped(false)
  }

  return (
    <Card className="w-full max-w-2xl mx-auto border-2 border-purple-200 bg-gradient-to-br from-purple-50 to-pink-50 dark:from-purple-950/20 dark:to-pink-950/20">
      <CardHeader className="text-center bg-purple-100 dark:bg-purple-900/30 rounded-t-lg">
        <CardTitle className="flex items-center justify-center gap-2 text-purple-700 dark:text-purple-300">
          <Brain className="h-6 w-6" />
          Flashcards - Card {currentIndex + 1} of {flashcards.length}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6 p-6">
        <div
          className="relative h-64 bg-white dark:bg-gray-900 rounded-xl border-2 border-purple-200 dark:border-purple-800 cursor-pointer transition-all duration-500 hover:shadow-xl transform hover:scale-[1.02] perspective-1000"
          onClick={() => setIsFlipped(!isFlipped)}
          style={{
            transformStyle: "preserve-3d",
            transform: isFlipped ? "rotateY(180deg)" : "rotateY(0deg)",
          }}
        >
          {/* Front of card */}
          <div
            className={`absolute inset-0 flex flex-col items-center justify-center p-6 backface-hidden ${isFlipped ? "opacity-0" : "opacity-100"}`}
          >
            <div className="text-center">
              <Badge variant="outline" className="mb-4 bg-purple-100 text-purple-700">
                Front
              </Badge>
              <p className="text-xl font-medium leading-relaxed text-center">{flashcards[currentIndex].front}</p>
            </div>
            <div className="absolute bottom-4 right-4">
              <Eye className="h-5 w-5 text-purple-400" />
            </div>
          </div>

          {/* Back of card */}
          <div
            className={`absolute inset-0 flex flex-col items-center justify-center p-6 backface-hidden ${isFlipped ? "opacity-100" : "opacity-0"}`}
            style={{ transform: "rotateY(180deg)" }}
          >
            <div className="text-center">
              <Badge variant="outline" className="mb-4 bg-green-100 text-green-700">
                Back
              </Badge>
              <p className="text-xl font-medium leading-relaxed text-center">{flashcards[currentIndex].back}</p>
            </div>
            <div className="absolute bottom-4 right-4">
              <EyeOff className="h-5 w-5 text-green-400" />
            </div>
          </div>
        </div>

        <div className="text-center">
          <p className="text-sm text-muted-foreground mb-4">Click the card to flip • Use arrows to navigate</p>
        </div>

        <div className="flex justify-between items-center">
          <Button variant="outline" onClick={prevCard} disabled={flashcards.length <= 1} size="lg">
            <ChevronLeft className="h-4 w-4 mr-2" />
            Previous
          </Button>

          <div className="flex gap-2">
            <Button variant="ghost" size="sm" onClick={() => onAction?.("download")}>
              <Download className="h-4 w-4" />
            </Button>
            <Button variant="ghost" size="sm" onClick={() => onAction?.("share")}>
              <Share className="h-4 w-4" />
            </Button>
          </div>

          <Button variant="outline" onClick={nextCard} disabled={flashcards.length <= 1} size="lg">
            Next
            <ChevronRight className="h-4 w-4 ml-2" />
          </Button>
        </div>

        <Progress value={((currentIndex + 1) / flashcards.length) * 100} className="h-3" />
      </CardContent>
    </Card>
  )
}

// Quiz Component
interface QuizQuestion {
  question: string
  options: string[]
  answer: string
  type?: "multiple_choice" | "true_false" | "fill_blank"
  explanation?: string
  topic?: string
}

interface QuizComponentProps {
  questions: QuizQuestion[]
  onAction?: (action: string) => void
  pdfId?: string
  userId?: string
  topic?: string
  sessionId?: string
  isDiagnostic?: boolean
}

export function QuizComponent({ 
  questions, 
  onAction, 
  pdfId, 
  userId, 
  topic, 
  sessionId, 
  isDiagnostic = false 
}: QuizComponentProps) {
  const [currentQuestion, setCurrentQuestion] = useState(0)
  const [selectedAnswers, setSelectedAnswers] = useState<string[]>(new Array(questions.length).fill(""))
  const [showResults, setShowResults] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [diagnosticResults, setDiagnosticResults] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)

  console.log("QuizComponent props:", { pdfId, userId, topic, sessionId, isDiagnostic, questionsCount: questions.length })

  const handleAnswerSelect = (answer: string) => {
    const newAnswers = [...selectedAnswers]
    newAnswers[currentQuestion] = answer
    setSelectedAnswers(newAnswers)
  }

  const nextQuestion = () => {
    if (currentQuestion < questions.length - 1) {
      setCurrentQuestion(currentQuestion + 1)
    } else {
      setShowResults(true)
      // Process diagnostic results if this is a diagnostic quiz
      console.log("Quiz completed. isDiagnostic:", isDiagnostic, "pdfId:", pdfId, "userId:", userId, "sessionId:", sessionId)
      console.log("All props check:", { 
        isDiagnostic, 
        hasPdfId: !!pdfId, 
        hasUserId: !!userId, 
        hasSessionId: !!sessionId,
        allPresent: isDiagnostic && pdfId && userId && sessionId
      })
      if (isDiagnostic && pdfId && userId && sessionId) {
        console.log("Processing diagnostic results...")
        processDiagnosticResults()
      } else {
        console.log("Not processing diagnostic results - missing required data")
        console.log("Missing:", {
          isDiagnostic: !isDiagnostic,
          pdfId: !pdfId,
          userId: !userId,
          sessionId: !sessionId
        })
      }
    }
  }

  const processDiagnosticResults = async () => {
    if (!pdfId || !userId || !sessionId) {
      console.log("Missing required data for diagnostic processing:", { pdfId, userId, sessionId })
      return
    }

    console.log("Starting diagnostic results processing with:", { pdfId, userId, sessionId, topic })
    setIsProcessing(true)
    setError(null)

    try {
      // Prepare user answers for processing
      const userAnswers = questions.map((q, index) => ({
        question_index: index,
        selected_answer: selectedAnswers[index] || "",
        is_correct: selectedAnswers[index] === q.answer
      }))

      console.log("User answers prepared:", userAnswers)

      const response = await agenticAPI.processDiagnosticResults({
        pdf_id: pdfId,
        user_id: userId,
        topic: topic || "",
        user_answers: userAnswers,
        session_id: sessionId
      })

      console.log("Diagnostic results API response:", response)
      if (response.status === "success" || response.results) {
        // The backend returns nested results, so we need to extract the actual results
        const backendResults = response.results as any
        const actualResults = backendResults.results || backendResults
        const remediation = backendResults.remediation || {}
        const masteryUpdate = backendResults.mastery_update || {}
        
        // Transform the backend response to match frontend expectations
        const transformedResults = {
          mastery_after: {
            overall: actualResults.overall_score || 0,
            topic_scores: masteryUpdate.topic_scores || {}
          },
          skill_gaps: actualResults.weak_areas || [],
          recommendations: remediation.recommendations || [],
          next_steps: backendResults.next_steps || [],
          improvement_score: actualResults.improvement_potential || 0
        }
        
        setDiagnosticResults(transformedResults)
        console.log("Diagnostic results set:", transformedResults)
      } else {
        console.log("Diagnostic results processing failed:", response)
        setError("Failed to process diagnostic results")
      }
    } catch (err) {
      setError("An error occurred while processing your results")
      console.error("Diagnostic processing error:", err)
    } finally {
      setIsProcessing(false)
    }
  }

  const resetQuiz = () => {
    setCurrentQuestion(0)
    setSelectedAnswers(new Array(questions.length).fill(""))
    setShowResults(false)
    setDiagnosticResults(null)
    setError(null)
    setIsProcessing(false)
  }

  const correctAnswers = selectedAnswers.filter((answer, index) => answer === questions[index].answer).length
  const score = Math.round((correctAnswers / questions.length) * 100)

  if (showResults) {
    return (
      <Card className="w-full max-w-3xl mx-auto border-2 border-green-200 bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-950/20 dark:to-emerald-950/20">
        <CardHeader className="text-center bg-green-100 dark:bg-green-900/30 rounded-t-lg">
          <CardTitle className="flex items-center justify-center gap-2 text-green-700 dark:text-green-300">
            <Target className="h-6 w-6" />
            {isDiagnostic ? "Diagnostic Complete!" : "Quiz Complete!"} 🎉
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6 p-6">
          <div className="text-center">
            <div className="text-5xl font-bold text-green-600 mb-2">{score}%</div>
            <p className="text-lg text-muted-foreground">
              You scored {correctAnswers} out of {questions.length} questions correctly!
            </p>
            <Badge variant={score >= 80 ? "default" : score >= 60 ? "secondary" : "destructive"} className="mt-2">
              {score >= 80 ? "Excellent!" : score >= 60 ? "Good Job!" : "Keep Learning!"}
            </Badge>
          </div>

          {/* Processing State */}
          {isProcessing && (
            <div className="flex items-center gap-2 p-4 border border-blue-200 bg-blue-50 dark:bg-blue-950/20 rounded-lg">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span className="text-sm">
                Processing your diagnostic results and generating personalized recommendations...
              </span>
            </div>
          )}

          {/* Error State */}
          {error && (
            <div className="flex items-center gap-2 p-4 border border-red-200 bg-red-50 dark:bg-red-950/20 rounded-lg text-red-700 dark:text-red-300">
              <AlertTriangle className="h-4 w-4" />
              <span className="text-sm">{error}</span>
            </div>
          )}

          {/* Diagnostic Results */}
          {diagnosticResults && (
            <div className="space-y-4">
              <Separator />
              <h3 className="text-lg font-semibold flex items-center gap-2">
                <Brain className="h-5 w-5" />
                Personalized Learning Analysis
              </h3>
              
              {/* Mastery Score */}
              {diagnosticResults.mastery_after && (
                <Card className="p-4 bg-blue-50 dark:bg-blue-950/20">
                  <div className="flex items-center gap-2 mb-2">
                    <TrendingUp className="h-5 w-5 text-blue-600" />
                    <span className="font-medium">Mastery Level</span>
                  </div>
                  <div className="text-2xl font-bold text-blue-600">
                    {Math.round(diagnosticResults.mastery_after.overall * 100)}%
                  </div>
                  <Progress value={diagnosticResults.mastery_after.overall * 100} className="mt-2" />
                </Card>
              )}

              {/* Skill Gaps */}
              {diagnosticResults.skill_gaps && diagnosticResults.skill_gaps.length > 0 && (
                <Card className="p-4 bg-orange-50 dark:bg-orange-950/20">
                  <div className="flex items-center gap-2 mb-3">
                    <AlertTriangle className="h-5 w-5 text-orange-600" />
                    <span className="font-medium">Areas for Improvement</span>
                  </div>
                  <div className="space-y-2">
                    {diagnosticResults.skill_gaps.map((gap: string, index: number) => (
                      <Badge key={index} variant="outline" className="mr-2 mb-2">
                        {gap}
                      </Badge>
                    ))}
                  </div>
                </Card>
              )}

              {/* Recommendations */}
              {diagnosticResults.recommendations && diagnosticResults.recommendations.length > 0 && (
                <Card className="p-4 bg-green-50 dark:bg-green-950/20">
                  <div className="flex items-center gap-2 mb-3">
                    <Lightbulb className="h-5 w-5 text-green-600" />
                    <span className="font-medium">Personalized Recommendations</span>
                  </div>
                  <ul className="space-y-2">
                    {diagnosticResults.recommendations.map((rec: string, index: number) => (
                      <li key={index} className="flex items-start gap-2">
                        <span className="text-green-600 mt-1">•</span>
                        <span className="text-sm">{rec}</span>
                      </li>
                    ))}
                  </ul>
                </Card>
              )}

              {/* Next Steps */}
              {diagnosticResults.next_steps && diagnosticResults.next_steps.length > 0 && (
                <Card className="p-4 bg-purple-50 dark:bg-purple-950/20">
                  <div className="flex items-center gap-2 mb-3">
                    <Workflow className="h-5 w-5 text-purple-600" />
                    <span className="font-medium">Next Steps</span>
                  </div>
                  <ul className="space-y-2">
                    {diagnosticResults.next_steps.map((step: string, index: number) => (
                      <li key={index} className="flex items-start gap-2">
                        <span className="text-purple-600 mt-1">{index + 1}.</span>
                        <span className="text-sm">{step}</span>
                      </li>
                    ))}
                  </ul>
                </Card>
              )}

              {/* Improvement Score */}
              {diagnosticResults.improvement_score && (
                <Card className="p-4 bg-indigo-50 dark:bg-indigo-950/20">
                  <div className="flex items-center gap-2 mb-2">
                    <Target className="h-5 w-5 text-indigo-600" />
                    <span className="font-medium">Improvement Potential</span>
                  </div>
                  <div className="text-2xl font-bold text-indigo-600">
                    +{Math.round(diagnosticResults.improvement_score * 100)}%
                  </div>
                  <p className="text-sm text-muted-foreground mt-1">
                    Your potential for improvement in this topic
                  </p>
                </Card>
              )}
            </div>
          )}

          <Progress value={score} className="h-4 bg-gray-200" />

          <div className="space-y-4">
            <h3 className="font-semibold text-lg">Review Your Answers:</h3>
            {questions.map((q, index) => (
              <Card
                key={index}
                className={`p-4 ${selectedAnswers[index] === q.answer ? "border-green-300 bg-green-50 dark:bg-green-950/20" : "border-red-300 bg-red-50 dark:bg-red-950/20"}`}
              >
                <div className="flex items-start gap-3">
                  {selectedAnswers[index] === q.answer ? (
                    <CheckCircle className="h-6 w-6 text-green-600 mt-1 shrink-0" />
                  ) : (
                    <XCircle className="h-6 w-6 text-red-600 mt-1 shrink-0" />
                  )}
                  <div className="flex-1">
                    <p className="font-medium mb-2">
                      Q{index + 1}: {q.question}
                    </p>
                    <div className="space-y-1 text-sm">
                      <div className="flex items-center gap-2">
                        <span className="text-muted-foreground">Your answer:</span>
                        <Badge variant={selectedAnswers[index] === q.answer ? "default" : "destructive"}>
                          {selectedAnswers[index] || "Not answered"}
                        </Badge>
                      </div>
                      {selectedAnswers[index] !== q.answer && (
                        <div className="flex items-center gap-2">
                          <span className="text-muted-foreground">Correct answer:</span>
                          <Badge variant="default" className="bg-green-600">
                            {q.answer}
                          </Badge>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </Card>
            ))}
          </div>

          <div className="flex justify-center gap-3 pt-4">
            <Button onClick={resetQuiz} variant="outline" size="lg">
              <RotateCcw className="h-4 w-4 mr-2" />
              Retake Quiz
            </Button>
            {isDiagnostic && !diagnosticResults && !isProcessing && (
              <Button onClick={processDiagnosticResults} variant="default" size="lg">
                <Brain className="h-4 w-4 mr-2" />
                Get Recommendations
              </Button>
            )}
            <Button onClick={() => onAction?.("download")} variant="outline" size="lg">
              <Download className="h-4 w-4 mr-2" />
              Download Results
            </Button>
            <Button onClick={() => onAction?.("share")} variant="outline" size="lg">
              <Share className="h-4 w-4 mr-2" />
              Share Results
            </Button>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="w-full max-w-3xl mx-auto border-2 border-blue-200 bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-950/20 dark:to-indigo-950/20">
      <CardHeader className="bg-blue-100 dark:bg-blue-900/30 rounded-t-lg">
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-blue-700 dark:text-blue-300">
            <Target className="h-6 w-6" />
            Quiz Question {currentQuestion + 1} of {questions.length}
          </div>
          <Badge variant="outline" className="text-lg px-3 py-1">
            {Math.round(((currentQuestion + 1) / questions.length) * 100)}%
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6 p-6">
        <Card className="p-6 bg-gradient-to-r from-blue-100 to-purple-100 dark:from-blue-900/30 dark:to-purple-900/30 border-l-4 border-blue-500">
          <p className="text-lg font-medium leading-relaxed">{questions[currentQuestion].question}</p>
        </Card>

        <div className="space-y-3">
          <h4 className="font-semibold text-muted-foreground">Choose your answer:</h4>
          {questions[currentQuestion].options.map((option, index) => (
            <Button
              key={index}
              variant={selectedAnswers[currentQuestion] === option ? "default" : "outline"}
              className={`w-full justify-start text-left h-auto p-4 transition-all duration-200 ${
                selectedAnswers[currentQuestion] === option
                  ? "bg-blue-600 hover:bg-blue-700 text-white shadow-lg"
                  : "hover:bg-blue-50 dark:hover:bg-blue-950/20 hover:border-blue-300"
              }`}
              onClick={() => handleAnswerSelect(option)}
            >
              <div className="flex items-center gap-4 w-full">
                <div
                  className={`w-8 h-8 rounded-full border-2 flex items-center justify-center text-sm font-bold ${
                    selectedAnswers[currentQuestion] === option
                      ? "border-white bg-white text-blue-600"
                      : "border-blue-300 text-blue-600"
                  }`}
                >
                  {String.fromCharCode(65 + index)}
                </div>
                <span className="flex-1 text-base">{option}</span>
              </div>
            </Button>
          ))}
        </div>

        <div className="flex justify-between items-center pt-6 border-t">
          <Button
            variant="outline"
            onClick={() => setCurrentQuestion(Math.max(0, currentQuestion - 1))}
            disabled={currentQuestion === 0}
            size="lg"
          >
            <ChevronLeft className="h-4 w-4 mr-2" />
            Previous
          </Button>

          <div className="flex-1 mx-6">
            <Progress value={((currentQuestion + 1) / questions.length) * 100} className="h-3" />
            <p className="text-center text-sm text-muted-foreground mt-2">
              Question {currentQuestion + 1} of {questions.length}
            </p>
          </div>

          <Button
            onClick={nextQuestion}
            disabled={!selectedAnswers[currentQuestion]}
            className="bg-blue-600 hover:bg-blue-700"
            size="lg"
          >
            {currentQuestion === questions.length - 1 ? "Finish Quiz" : "Next Question"}
            <ChevronRight className="h-4 w-4 ml-2" />
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

// Diagnostic Component
interface DiagnosticQuestion {
  question: string
  options: string[]
  answer: string
  type?: "multiple_choice" | "true_false" | "fill_blank"
  explanation?: string
  topic?: string
}

interface DiagnosticComponentProps {
  questions: DiagnosticQuestion[]
  onAction?: (action: string) => void
  pdfId?: string
  userId?: string
  topic?: string
  sessionId?: string
}

export function DiagnosticComponent({ 
  questions, 
  onAction, 
  pdfId, 
  userId, 
  topic, 
  sessionId
}: DiagnosticComponentProps) {
  const [currentQuestion, setCurrentQuestion] = useState(0)
  const [selectedAnswers, setSelectedAnswers] = useState<string[]>(new Array(questions.length).fill(""))
  const [showResults, setShowResults] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [diagnosticResults, setDiagnosticResults] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)

  const handleAnswerSelect = (answer: string) => {
    const newAnswers = [...selectedAnswers]
    newAnswers[currentQuestion] = answer
    setSelectedAnswers(newAnswers)
  }

  const nextQuestion = () => {
    if (currentQuestion < questions.length - 1) {
      setCurrentQuestion(currentQuestion + 1)
    } else {
      setShowResults(true)
      // Always process diagnostic results when quiz is completed
      processDiagnosticResults()
    }
  }

  const processDiagnosticResults = async () => {
    setIsProcessing(true)
    setError(null)

    try {
      // Calculate basic results from the quiz
      const correctAnswers = questions.filter((q, index) => selectedAnswers[index] === q.answer).length
      const totalQuestions = questions.length
      const score = correctAnswers / totalQuestions

      // If we have the required parameters, try to get AI-powered results
      if (pdfId && userId && sessionId) {
        try {
          const userAnswers = questions.map((q, index) => ({
            question_index: index,
            selected_answer: selectedAnswers[index] || "",
            is_correct: selectedAnswers[index] === q.answer
          }))

          const response = await agenticAPI.processDiagnosticResults({
            pdf_id: pdfId,
            user_id: userId,
            topic: topic || "",
            user_answers: userAnswers,
            session_id: sessionId
          })

          if (response.status === "success" || response.results) {
            const backendResults = response.results as any
            const actualResults = backendResults.results || backendResults
            const remediation = backendResults.remediation || {}
            const masteryUpdate = backendResults.mastery_update || {}
            
            const transformedResults = {
              mastery_after: {
                overall: actualResults.overall_score || score,
                topic_scores: masteryUpdate.topic_scores || {}
              },
              skill_gaps: actualResults.weak_areas || [],
              recommendations: remediation.recommendations || [],
              next_steps: backendResults.next_steps || [],
              improvement_score: actualResults.improvement_potential || 0
            }
            
            setDiagnosticResults(transformedResults)
            return
          }
        } catch (apiError) {
          console.warn("AI diagnostic processing failed, using fallback:", apiError)
        }
      }

      // Fallback: Generate comprehensive diagnostic results
      const incorrectQuestions = questions.filter((q, index) => selectedAnswers[index] !== q.answer)
      const correctQuestions = questions.filter((q, index) => selectedAnswers[index] === q.answer)
      
      // Analyze performance by topic
      const topicPerformance: { [key: string]: { correct: number; total: number } } = {}
      questions.forEach((q, index) => {
        const topic = q.topic || "General Knowledge"
        if (!topicPerformance[topic]) {
          topicPerformance[topic] = { correct: 0, total: 0 }
        }
        topicPerformance[topic].total++
        if (selectedAnswers[index] === q.answer) {
          topicPerformance[topic].correct++
        }
      })
      
      const skillGaps = Object.entries(topicPerformance)
        .filter(([_, perf]) => perf.correct / perf.total < 0.7)
        .map(([topic, _]) => topic)
      
      const strongAreas = Object.entries(topicPerformance)
        .filter(([_, perf]) => perf.correct / perf.total >= 0.8)
        .map(([topic, _]) => topic)
      
      // Generate specific recommendations based on performance
      const recommendations = []
      
      if (score < 0.4) {
        recommendations.push("📚 **Foundation Review**: Start with basic concepts and build up gradually")
        recommendations.push("🎯 **Focused Study**: Dedicate 30-45 minutes daily to core topics")
        recommendations.push("📖 **Multiple Resources**: Use different learning materials to reinforce understanding")
      } else if (score < 0.7) {
        recommendations.push("🔍 **Targeted Practice**: Focus on specific weak areas identified in the assessment")
        recommendations.push("💡 **Concept Mapping**: Create visual diagrams to connect related ideas")
        recommendations.push("🔄 **Active Recall**: Test yourself regularly on the material")
      } else {
        recommendations.push("🚀 **Advanced Topics**: Challenge yourself with more complex material")
        recommendations.push("👥 **Peer Teaching**: Explain concepts to others to deepen understanding")
        recommendations.push("🎓 **Application Focus**: Apply knowledge to real-world scenarios")
      }
      
      // Add topic-specific recommendations
      if (skillGaps.includes("comprehension")) {
        recommendations.push("📝 **Reading Strategy**: Practice active reading with note-taking and summarization")
      }
      if (skillGaps.includes("analysis")) {
        recommendations.push("🔬 **Critical Thinking**: Work on breaking down complex information into smaller parts")
      }
      if (skillGaps.includes("application")) {
        recommendations.push("🛠️ **Practical Exercises**: Focus on hands-on practice and real-world applications")
      }
      
      const nextSteps = [
        `📊 **Retake Assessment**: Test again in ${score < 0.5 ? '1 week' : '3-5 days'} to measure progress`,
        "📚 **Study Plan**: Create a structured study schedule focusing on weak areas",
        "🎯 **Practice Tests**: Take regular practice quizzes to reinforce learning",
        "📖 **Resource Review**: Revisit the original material with a focus on missed concepts"
      ]
      
      if (strongAreas.length > 0) {
        nextSteps.push(`⭐ **Leverage Strengths**: Use your strong areas (${strongAreas.join(", ")}) to build confidence`)
      }

      const fallbackResults = {
        mastery_after: {
          overall: score,
          topic_scores: {}
        },
        skill_gaps: skillGaps,
        recommendations: recommendations,
        next_steps: nextSteps,
        improvement_score: Math.round((1 - score) * 100)
      }
      
      setDiagnosticResults(fallbackResults)
    } catch (err) {
      console.error("Diagnostic processing error:", err)
      setError("Failed to process diagnostic results. Please try again.")
    } finally {
      setIsProcessing(false)
    }
  }

  if (showResults) {
    return (
      <Card className="w-full max-w-4xl mx-auto border-2 border-orange-200 bg-gradient-to-br from-orange-50 to-red-50 dark:from-orange-950/20 dark:to-red-950/20">
        <CardHeader className="bg-orange-100 dark:bg-orange-900/30 rounded-t-lg">
          <CardTitle className="flex items-center gap-2 text-orange-700 dark:text-orange-300">
            <Target className="h-6 w-6" />
            Diagnostic Assessment Results
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6 p-6">
          {/* Processing State */}
          {isProcessing && (
            <div className="flex items-center gap-2 p-4 border border-blue-200 bg-blue-50 dark:bg-blue-950/20 rounded-lg">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span className="text-sm">
                Processing your diagnostic results and generating personalized recommendations...
              </span>
            </div>
          )}

          {/* Error State */}
          {error && (
            <div className="flex items-center gap-2 p-4 border border-red-200 bg-red-50 dark:bg-red-950/20 rounded-lg text-red-700 dark:text-red-300">
              <AlertTriangle className="h-4 w-4" />
              <span className="text-sm">{error}</span>
            </div>
          )}

          {/* Diagnostic Results */}
          {diagnosticResults && (
            <div className="space-y-4">
              <Separator />
              <h3 className="text-lg font-semibold flex items-center gap-2">
                <Brain className="h-5 w-5" />
                Personalized Learning Analysis
              </h3>
              
              {/* Mastery Score */}
              {diagnosticResults.mastery_after && (
                <Card className="p-4 bg-blue-50 dark:bg-blue-950/20">
                  <div className="flex items-center gap-2 mb-2">
                    <TrendingUp className="h-5 w-5 text-blue-600" />
                    <span className="font-medium">Mastery Level</span>
                  </div>
                  <div className="text-2xl font-bold text-blue-600">
                    {Math.round(diagnosticResults.mastery_after.overall * 100)}%
                  </div>
                  <Progress value={diagnosticResults.mastery_after.overall * 100} className="mt-2" />
                </Card>
              )}

              {/* Correct Answers Review */}
              <Card className="p-4 bg-gray-50 dark:bg-gray-950/20">
                <div className="flex items-center gap-2 mb-3">
                  <CheckCircle className="h-5 w-5 text-gray-600" />
                  <span className="font-medium">Answer Review</span>
                </div>
                <div className="space-y-3">
                  {questions.map((question, index) => {
                    const userAnswer = selectedAnswers[index] || "No answer"
                    const isCorrect = userAnswer === question.answer
                    return (
                      <div key={index} className="p-3 bg-white dark:bg-gray-800 rounded-lg border">
                        <div className="flex items-start gap-3">
                          <div className={`w-6 h-6 rounded-full flex items-center justify-center text-sm font-bold ${
                            isCorrect 
                              ? "bg-green-100 text-green-600 border border-green-300" 
                              : "bg-red-100 text-red-600 border border-red-300"
                          }`}>
                            {index + 1}
                          </div>
                          <div className="flex-1">
                            <p className="font-medium text-sm mb-2">{question.question}</p>
                            <div className="space-y-1">
                              <div className="flex items-center gap-2">
                                <span className="text-xs text-gray-500">Your answer:</span>
                                <span className={`text-sm px-2 py-1 rounded ${
                                  isCorrect 
                                    ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300" 
                                    : "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300"
                                }`}>
                                  {userAnswer}
                                </span>
                              </div>
                              <div className="flex items-center gap-2">
                                <span className="text-xs text-gray-500">Correct answer:</span>
                                <span className="text-sm px-2 py-1 rounded bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300">
                                  {question.answer}
                                </span>
                              </div>
                              {question.explanation && (
                                <div className="mt-2 p-2 bg-gray-100 dark:bg-gray-700 rounded text-xs text-gray-600 dark:text-gray-300">
                                  <strong>Explanation:</strong> {question.explanation}
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    )
                  })}
                </div>
              </Card>

              {/* Skill Gaps */}
              {diagnosticResults.skill_gaps && diagnosticResults.skill_gaps.length > 0 && (
                <Card className="p-4 bg-orange-50 dark:bg-orange-950/20">
                  <div className="flex items-center gap-2 mb-3">
                    <AlertTriangle className="h-5 w-5 text-orange-600" />
                    <span className="font-medium">Areas for Improvement</span>
                  </div>
                  <div className="space-y-2">
                    {diagnosticResults.skill_gaps.map((gap: string, index: number) => (
                      <Badge key={index} variant="outline" className="mr-2 mb-2">
                        {gap}
                      </Badge>
                    ))}
                  </div>
                </Card>
              )}

              {/* Recommendations */}
              {diagnosticResults.recommendations && diagnosticResults.recommendations.length > 0 && (
                <Card className="p-4 bg-green-50 dark:bg-green-950/20">
                  <div className="flex items-center gap-2 mb-3">
                    <Lightbulb className="h-5 w-5 text-green-600" />
                    <span className="font-medium">Personalized Recommendations</span>
                  </div>
                  <ul className="space-y-2">
                    {diagnosticResults.recommendations.map((rec: string, index: number) => (
                      <li key={index} className="flex items-start gap-2">
                        <span className="text-green-600 mt-1">•</span>
                        <span className="text-sm">{rec}</span>
                      </li>
                    ))}
                  </ul>
                </Card>
              )}

              {/* Next Steps */}
              {diagnosticResults.next_steps && diagnosticResults.next_steps.length > 0 && (
                <Card className="p-4 bg-purple-50 dark:bg-purple-950/20">
                  <div className="flex items-center gap-2 mb-3">
                    <Workflow className="h-5 w-5 text-purple-600" />
                    <span className="font-medium">Next Steps</span>
                  </div>
                  <ul className="space-y-2">
                    {diagnosticResults.next_steps.map((step: string, index: number) => (
                      <li key={index} className="flex items-start gap-2">
                        <span className="text-purple-600 mt-1">{index + 1}.</span>
                        <span className="text-sm">{step}</span>
                      </li>
                    ))}
                  </ul>
                </Card>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="w-full max-w-3xl mx-auto border-2 border-orange-200 bg-gradient-to-br from-orange-50 to-red-50 dark:from-orange-950/20 dark:to-red-950/20">
      <CardHeader className="bg-orange-100 dark:bg-orange-900/30 rounded-t-lg">
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-orange-700 dark:text-orange-300">
            <Target className="h-6 w-6" />
            Diagnostic Question {currentQuestion + 1} of {questions.length}
          </div>
          <Badge variant="outline" className="text-lg px-3 py-1">
            {Math.round(((currentQuestion + 1) / questions.length) * 100)}%
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6 p-6">
        <Card className="p-6 bg-gradient-to-r from-orange-100 to-red-100 dark:from-orange-900/30 dark:to-red-900/30 border-l-4 border-orange-500">
          <p className="text-lg font-medium leading-relaxed">{questions[currentQuestion].question}</p>
        </Card>

        <div className="space-y-3">
          <h4 className="font-semibold text-muted-foreground">
            {questions[currentQuestion].type === "true_false" ? "True or False:" :
             questions[currentQuestion].type === "fill_blank" ? "Fill in the blank:" :
             "Choose your answer:"}
          </h4>
          
          {/* Multiple Choice Questions */}
          {questions[currentQuestion].type === "multiple_choice" && questions[currentQuestion].options.map((option, index) => (
            <Button
              key={index}
              variant={selectedAnswers[currentQuestion] === option ? "default" : "outline"}
              className={`w-full justify-start text-left h-auto p-4 transition-all duration-200 ${
                selectedAnswers[currentQuestion] === option
                  ? "bg-orange-600 hover:bg-orange-700 text-white shadow-lg"
                  : "hover:bg-orange-50 dark:hover:bg-orange-950/20 hover:border-orange-300"
              }`}
              onClick={() => handleAnswerSelect(option)}
            >
              <div className="flex items-center gap-4 w-full">
                <div
                  className={`w-8 h-8 rounded-full border-2 flex items-center justify-center text-sm font-bold ${
                    selectedAnswers[currentQuestion] === option
                      ? "border-white bg-white text-orange-600"
                      : "border-orange-300 text-orange-600"
                  }`}
                >
                  {String.fromCharCode(65 + index)}
                </div>
                <span className="flex-1 text-base">{option}</span>
              </div>
            </Button>
          ))}
          
          {/* True/False Questions */}
          {questions[currentQuestion].type === "true_false" && (
            <div className="grid grid-cols-2 gap-4">
              <Button
                variant={selectedAnswers[currentQuestion] === "True" ? "default" : "outline"}
                className={`h-16 text-lg transition-all duration-200 ${
                  selectedAnswers[currentQuestion] === "True"
                    ? "bg-green-600 hover:bg-green-700 text-white shadow-lg"
                    : "hover:bg-green-50 dark:hover:bg-green-950/20"
                }`}
                onClick={() => handleAnswerSelect("True")}
              >
                ✓ True
              </Button>
              <Button
                variant={selectedAnswers[currentQuestion] === "False" ? "default" : "outline"}
                className={`h-16 text-lg transition-all duration-200 ${
                  selectedAnswers[currentQuestion] === "False"
                    ? "bg-red-600 hover:bg-red-700 text-white shadow-lg"
                    : "hover:bg-red-50 dark:hover:bg-red-950/20"
                }`}
                onClick={() => handleAnswerSelect("False")}
              >
                ✗ False
              </Button>
            </div>
          )}
          
          {/* Fill in the Blank Questions */}
          {questions[currentQuestion].type === "fill_blank" && (
            <div className="space-y-4">
              <div className="p-4 bg-gray-50 dark:bg-gray-900/50 rounded-lg border-2 border-dashed border-gray-300 dark:border-gray-700">
                <p className="text-sm text-muted-foreground mb-2">Type your answer below:</p>
                <input
                  type="text"
                  value={selectedAnswers[currentQuestion] || ""}
                  onChange={(e) => handleAnswerSelect(e.target.value)}
                  placeholder="Enter your answer here..."
                  className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                />
              </div>
              {questions[currentQuestion].explanation && (
                <div className="p-3 bg-orange-50 dark:bg-orange-950/20 rounded-lg">
                  <p className="text-sm text-orange-700 dark:text-orange-300">
                    <strong>Hint:</strong> {questions[currentQuestion].explanation}
                  </p>
                </div>
              )}
            </div>
          )}
        </div>

        <div className="flex justify-between items-center pt-6 border-t">
          <Button
            variant="outline"
            onClick={() => setCurrentQuestion(Math.max(0, currentQuestion - 1))}
            disabled={currentQuestion === 0}
            size="lg"
          >
            <ChevronLeft className="h-4 w-4 mr-2" />
            Previous
          </Button>

          <div className="flex-1 mx-6">
            <Progress value={((currentQuestion + 1) / questions.length) * 100} className="h-3" />
            <p className="text-center text-sm text-muted-foreground mt-2">
              Question {currentQuestion + 1} of {questions.length}
            </p>
          </div>

          <Button
            onClick={nextQuestion}
            disabled={!selectedAnswers[currentQuestion]}
            className="bg-orange-600 hover:bg-orange-700"
            size="lg"
          >
            {currentQuestion === questions.length - 1 ? "Finish Assessment" : "Next Question"}
            <ChevronRight className="h-4 w-4 ml-2" />
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

// Summary Component
interface SummaryComponentProps {
  summary: string
  keyPoints?: string[]
  onAction?: (action: string) => void
}

export function SummaryComponent({ summary, keyPoints, onAction }: SummaryComponentProps) {
  // Check if key points are meaningful and different from summary
  const hasMeaningfulKeyPoints = keyPoints && 
    keyPoints.length > 0 && 
    keyPoints.some(point => point.length > 20) &&
    keyPoints.some(point => !summary.toLowerCase().includes(point.toLowerCase().substring(0, 30)))

  return (
    <Card className="w-full max-w-3xl mx-auto border-2 border-blue-200 bg-gradient-to-br from-blue-50 to-cyan-50 dark:from-blue-950/20 dark:to-cyan-950/20">
      <CardHeader className="bg-blue-100 dark:bg-blue-900/30 rounded-t-lg">
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-blue-700 dark:text-blue-300">
            <FileText className="h-6 w-6" />
            Document Summary
          </div>
          <div className="flex gap-1">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onAction?.("copy")}
              className="hover:bg-blue-200 dark:hover:bg-blue-800"
            >
              <Copy className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onAction?.("download")}
              className="hover:bg-blue-200 dark:hover:bg-blue-800"
            >
              <Download className="h-4 w-4" />
            </Button>
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6 p-6">
        <div className="p-6 bg-gradient-to-r from-blue-100 to-indigo-100 dark:from-blue-900/30 dark:to-indigo-900/30 rounded-xl border-l-4 border-blue-500 shadow-sm">
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center shrink-0 mt-1">
              <FileText className="h-4 w-4 text-white" />
            </div>
            <div className="flex-1">
              <h3 className="font-semibold text-blue-800 dark:text-blue-200 mb-3">Summary Overview</h3>
              <p className="text-base leading-relaxed text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                {summary}
              </p>
            </div>
          </div>
        </div>

        {hasMeaningfulKeyPoints && (
          <>
            <Separator className="my-6" />
            <div className="space-y-4">
              <div className="flex items-center gap-2 mb-4">
                <CheckCircle className="h-5 w-5 text-green-600" />
                <h4 className="font-semibold text-lg text-green-700 dark:text-green-300">Key Insights & Action Items</h4>
              </div>
              <div className="grid gap-3">
                {keyPoints.slice(0, 5).map((point, index) => (
                  <div
                    key={index}
                    className="flex items-start gap-3 p-4 bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-950/20 dark:to-emerald-950/20 rounded-lg border-l-4 border-green-400 shadow-sm hover:shadow-md transition-shadow"
                  >
                    <div className="w-6 h-6 bg-gradient-to-r from-green-500 to-emerald-500 text-white rounded-full flex items-center justify-center text-sm font-bold shrink-0 mt-0.5">
                      {index + 1}
                    </div>
                    <div className="flex-1">
                      <span className="text-sm leading-relaxed text-gray-700 dark:text-gray-300 font-medium">{point}</span>
                    </div>
                  </div>
                ))}
              </div>
              {keyPoints.length > 5 && (
                <p className="text-xs text-muted-foreground text-center mt-2">
                  +{keyPoints.length - 5} more insights available
                </p>
              )}
            </div>
          </>
        )}

        <Separator className="my-6" />
        <div className="flex justify-between items-center text-sm text-muted-foreground bg-gray-50 dark:bg-gray-900/50 p-4 rounded-lg">
          <div className="flex items-center gap-4">
            <span>📖 Reading time: ~2 minutes</span>
            <span>📝 {summary.split(" ").length} words</span>
          </div>
          <Badge variant="outline" className="bg-blue-100 text-blue-700 border-blue-300">
            Summary Complete
          </Badge>
        </div>
      </CardContent>
    </Card>
  )
}

// Workflow Component
//
// Backend sends a structured `workflow_data` object (see distiller.py
// `_handle_workflow_generation`). For backward compatibility we still accept a
// plain string and parse it line-by-line. We deliberately do NOT fabricate a
// "Start Learning → Read Content → Take Quiz" fallback any more — when the
// backend can't ground a workflow we surface a clear empty state so the user
// retries with a better prompt instead of seeing fake content.
interface WorkflowStepData {
  step?: number
  title?: string
  description?: string
  inputs?: string[]
  outputs?: string[]
  tools?: string[]
  duration?: string
  common_pitfalls?: string[]
  decision?: string | null
  type?: string
}

interface WorkflowData {
  title?: string
  description?: string
  type?: string
  steps?: WorkflowStepData[]
  branches?: Array<{ from_step: number; condition: string; action: string }>
  prerequisites?: string[]
  deliverable?: string
  estimated_duration?: string
  mermaid_code?: string
}

interface WorkflowComponentProps {
  // Accepts either a JSON string of WorkflowData, a plain text fallback,
  // or the raw structured object passed straight through.
  workflow: string | WorkflowData
  onAction?: (action: string) => void
}

export function WorkflowComponent({ workflow, onAction }: WorkflowComponentProps) {
  const data: WorkflowData = (() => {
    if (typeof workflow !== "string") return workflow || {}
    // Try JSON
    try {
      const parsed = JSON.parse(workflow)
      if (parsed && typeof parsed === "object") return parsed as WorkflowData
    } catch {}
    // Fall back to line parsing — produce step titles only, no synthetic types.
    const steps: WorkflowStepData[] = workflow
      .split("\n")
      .map((l) => l.trim())
      .filter((l) => l && !l.startsWith("#"))
      .map((line, i) => ({
        step: i + 1,
        title: line.length > 80 ? line.slice(0, 80) + "…" : line,
        description: line,
      }))
    return { steps, title: "Workflow", description: "" }
  })()

  const workflowSteps = (data.steps || []).map((s, i) => ({
    id: `step-${s.step ?? i + 1}`,
    title: s.title || `Step ${i + 1}`,
    description: s.description || "",
    type: s.decision
      ? ("decision" as const)
      : i === 0
        ? ("start" as const)
        : i === (data.steps?.length || 1) - 1
          ? ("end" as const)
          : ("process" as const),
    inputs: s.inputs,
    outputs: s.outputs,
    tools: s.tools,
    duration: s.duration,
    pitfalls: s.common_pitfalls,
    decision: s.decision,
  }))

  const getStepIcon = (type: string) => {
    switch (type) {
      case 'start':
        return '🚀'
      case 'end':
        return '✅'
      case 'decision':
        return '❓'
      default:
        return '📋'
    }
  }

  const getStepColor = (type: string) => {
    switch (type) {
      case 'start':
        return 'bg-green-100 border-green-300 text-green-800 dark:bg-green-900/30 dark:border-green-700 dark:text-green-300'
      case 'end':
        return 'bg-blue-100 border-blue-300 text-blue-800 dark:bg-blue-900/30 dark:border-blue-700 dark:text-blue-300'
      case 'decision':
        return 'bg-yellow-100 border-yellow-300 text-yellow-800 dark:bg-yellow-900/30 dark:border-yellow-700 dark:text-yellow-300'
      default:
        return 'bg-indigo-100 border-indigo-300 text-indigo-800 dark:bg-indigo-900/30 dark:border-indigo-700 dark:text-indigo-300'
    }
  }

  if (!workflowSteps.length) {
    return (
      <Card className="w-full max-w-3xl mx-auto">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Workflow className="h-5 w-5 text-indigo-600" />
            {data.title || "Workflow"}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            We couldn't build a grounded workflow from this material. Try uploading a more detailed PDF, or
            ask a more specific question (e.g. "create a workflow for fine-tuning a Llama model").
          </p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="w-full max-w-6xl mx-auto">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Workflow className="h-5 w-5 text-indigo-600" />
            {data.title || "Workflow"}
          </div>
          <div className="flex gap-1">
            <Button variant="ghost" size="sm" onClick={() => onAction?.("copy")}>
              <Copy className="h-4 w-4" />
            </Button>
            <Button variant="ghost" size="sm" onClick={() => onAction?.("download")}>
              <Download className="h-4 w-4" />
            </Button>
          </div>
        </CardTitle>
        {data.description && (
          <p className="text-sm text-muted-foreground mt-1">{data.description}</p>
        )}
        {(data.estimated_duration || data.deliverable) && (
          <div className="mt-2 flex flex-wrap gap-2 text-xs">
            {data.estimated_duration && (
              <Badge variant="outline">⏱ {data.estimated_duration}</Badge>
            )}
            {data.deliverable && <Badge variant="outline">🎯 {data.deliverable}</Badge>}
          </div>
        )}
      </CardHeader>
      <CardContent>
        {data.prerequisites && data.prerequisites.length > 0 && (
          <div className="mb-4 p-3 rounded-lg bg-muted/40 text-sm">
            <span className="font-medium">Prerequisites: </span>
            {data.prerequisites.join(" · ")}
          </div>
        )}

        {/* Vertical step list with rich detail */}
        <div className="space-y-3">
          {workflowSteps.map((step, index) => (
            <div key={step.id} className="flex gap-3">
              <div className="flex flex-col items-center">
                <div
                  className={`w-9 h-9 rounded-full border-2 flex items-center justify-center text-sm font-bold ${getStepColor(step.type)}`}
                >
                  {index + 1}
                </div>
                {index < workflowSteps.length - 1 && (
                  <div className="w-0.5 flex-1 bg-indigo-200 dark:bg-indigo-800 mt-1" />
                )}
              </div>
              <div className={`flex-1 mb-2 rounded-lg border p-3 ${getStepColor(step.type)}`}>
                <div className="flex items-center gap-2 mb-1">
                  <span>{getStepIcon(step.type)}</span>
                  <span className="font-semibold text-sm">{step.title}</span>
                  {step.duration && (
                    <Badge variant="outline" className="text-[10px] ml-auto">
                      {step.duration}
                    </Badge>
                  )}
                </div>
                {step.description && (
                  <p className="text-xs opacity-90 mb-2">{step.description}</p>
                )}
                {step.decision && (
                  <p className="text-xs italic">↳ Decision: {step.decision}</p>
                )}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-2 mt-2">
                  {step.inputs && step.inputs.length > 0 && (
                    <div className="text-xs">
                      <span className="font-medium">Inputs: </span>
                      {step.inputs.join(", ")}
                    </div>
                  )}
                  {step.outputs && step.outputs.length > 0 && (
                    <div className="text-xs">
                      <span className="font-medium">Outputs: </span>
                      {step.outputs.join(", ")}
                    </div>
                  )}
                  {step.tools && step.tools.length > 0 && (
                    <div className="text-xs">
                      <span className="font-medium">Tools: </span>
                      {step.tools.join(", ")}
                    </div>
                  )}
                </div>
                {step.pitfalls && step.pitfalls.length > 0 && (
                  <div className="text-xs mt-2">
                    <span className="font-medium">⚠ Common pitfalls: </span>
                    {step.pitfalls.join("; ")}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>

        {data.branches && data.branches.length > 0 && (
          <div className="mt-4 p-3 rounded-lg bg-yellow-50 dark:bg-yellow-950/20 text-sm">
            <p className="font-medium mb-1">Alternative paths</p>
            <ul className="space-y-1 text-xs">
              {data.branches.map((b, i) => (
                <li key={i}>
                  ↳ From step {b.from_step}, if <em>{b.condition}</em> → {b.action}
                </li>
              ))}
            </ul>
          </div>
        )}

        {data.mermaid_code && (
          <details className="mt-4">
            <summary className="text-xs text-muted-foreground cursor-pointer">View Mermaid source</summary>
            <pre className="mt-2 p-2 bg-muted/40 rounded text-[10px] overflow-x-auto whitespace-pre-wrap">
              {data.mermaid_code}
            </pre>
          </details>
        )}
      </CardContent>
    </Card>
  )
}

// Lesson Component
interface LessonComponentProps {
  lesson: any
  onAction?: (action: string) => void
}

export function LessonComponent({ lesson, onAction }: LessonComponentProps) {
  const parseLessonContent = (lessonData: any) => {
    if (typeof lessonData === "string") {
      return {
        title: "Structured Lesson",
        content: lessonData,
        objectives: ["Master the key concepts", "Apply knowledge effectively", "Build practical understanding"],
        sections: lessonData.split("\n\n").filter((section) => section.trim().length > 0),
      }
    }

    if (typeof lessonData === "object" && lessonData !== null) {
      return {
        title: lessonData.title || "Structured Lesson",
        content: lessonData.content || JSON.stringify(lessonData, null, 2),
        objectives: lessonData.objectives || lessonData.learning_objectives || ["Master the key concepts"],
        sections: lessonData.sections || [lessonData.content || JSON.stringify(lessonData, null, 2)],
      }
    }

    return {
      title: "Structured Lesson",
      content: "Lesson content will be displayed here.",
      objectives: ["Master the key concepts"],
      sections: ["Lesson content will be displayed here."],
    }
  }

  const parsedLesson = parseLessonContent(lesson)

  return (
    <Card className="w-full max-w-3xl mx-auto border-2 border-green-200 bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-950/20 dark:to-emerald-950/20">
      <CardHeader className="bg-green-100 dark:bg-green-900/30 rounded-t-lg">
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-green-700 dark:text-green-300">
            <BookOpen className="h-6 w-6" />
            Lesson Plan
          </div>
          <div className="flex gap-1">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onAction?.("copy")}
              className="hover:bg-green-200 dark:hover:bg-green-800"
            >
              <Copy className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onAction?.("download")}
              className="hover:bg-green-200 dark:hover:bg-green-800"
            >
              <Download className="h-4 w-4" />
            </Button>
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6 p-6">
        <div className="p-6 bg-gradient-to-r from-green-100 to-teal-100 dark:from-green-900/30 dark:to-teal-900/30 rounded-xl border-l-4 border-green-500 shadow-sm">
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center shrink-0 mt-1">
              <Target className="h-4 w-4 text-white" />
            </div>
            <div className="flex-1">
              <h3 className="font-semibold text-green-800 dark:text-green-200 mb-3">Learning Objectives</h3>
              <ul className="space-y-2">
                {parsedLesson.objectives.map((objective: string, index: number) => (
                  <li key={index} className="flex items-start gap-2 text-sm text-gray-700 dark:text-gray-300">
                    <CheckCircle className="h-4 w-4 text-green-600 mt-0.5 shrink-0" />
                    <span>{objective}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <div className="flex items-center gap-2 mb-4">
            <BookOpen className="h-5 w-5 text-green-600" />
            <h4 className="font-semibold text-lg text-green-700 dark:text-green-300">Lesson Content</h4>
          </div>

          <div className="space-y-4">
            {parsedLesson.sections.map((section: any, index: number) => (
              <div
                key={index}
                className="p-5 bg-white dark:bg-gray-900/50 rounded-lg border border-green-200 dark:border-green-800 shadow-sm"
              >
                <div className="flex items-start gap-3">
                  <div className="w-6 h-6 bg-green-500 text-white rounded-full flex items-center justify-center text-sm font-bold shrink-0 mt-1">
                    {index + 1}
                  </div>
                  <div className="flex-1">
                    <div className="prose prose-sm max-w-none">
                      <p className="text-base leading-relaxed text-gray-700 dark:text-gray-300 whitespace-pre-wrap m-0">
                        {section}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <Separator className="my-6" />

        <div className="bg-gradient-to-r from-green-50 to-blue-50 dark:from-green-950/30 dark:to-blue-950/30 p-5 rounded-lg border border-green-200 dark:border-green-800">
          <div className="flex justify-between items-center flex-wrap gap-4">
            <div className="flex items-center gap-6 text-sm text-muted-foreground">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                <span>⏱️ Estimated time: 15-20 minutes</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                <span>📚 {parsedLesson.sections.length} sections</span>
              </div>
            </div>
            <div className="flex gap-2">
              <Badge variant="outline" className="bg-green-100 text-green-700 border-green-300">
                Beginner Friendly
              </Badge>
              <Badge variant="outline" className="bg-blue-100 text-blue-700 border-blue-300">
                Interactive
              </Badge>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
