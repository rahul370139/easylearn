"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Check, ChevronsRight, Lightbulb, List, Brain, X } from "lucide-react"

interface Lesson {
  lesson_id: string
  bullets: string[]
  flashcards: Array<{ front: string; back: string }>
  quiz: Array<{ question: string; options: string[]; answer: string }>
  concept_map: any
  framework: string
  explanation_level: string
}

export function LessonDisplay({ lesson }: { lesson: Lesson }) {
  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex flex-wrap items-center gap-4">
          <CardTitle className="text-2xl flex-1">Your Generated Lesson</CardTitle>
          <Badge variant="outline">{lesson.framework}</Badge>
          <Badge variant="secondary">{lesson.explanation_level}</Badge>
        </div>
      </CardHeader>
      <CardContent>
        <Card>
          <CardHeader>
            <CardTitle>Key Points</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-3">
              {lesson.bullets.map((point, index) => (
                <li key={index} className="flex items-start gap-3">
                  <ChevronsRight className="h-5 w-5 text-primary mt-1 flex-shrink-0" />
                  <span className="text-muted-foreground">{point.replace("•", "")}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      </CardContent>
    </Card>
  )
}

export function FlashcardPlayer({ flashcards }: { flashcards: Array<{ front: string; back: string }> }) {
  const [currentIndex, setCurrentIndex] = useState(0)
  const [isFlipped, setIsFlipped] = useState(false)

  const handleNext = () => {
    setIsFlipped(false)
    setCurrentIndex((prev) => (prev + 1) % flashcards.length)
  }

  if (!flashcards || flashcards.length === 0) {
    return <p>No flashcards available.</p>
  }

  const card = flashcards[currentIndex]

  return (
    <div className="space-y-4">
      <div
        className="relative w-full h-64 cursor-pointer rounded-lg border bg-card text-card-foreground shadow-sm p-6 flex items-center justify-center text-center"
        onClick={() => setIsFlipped(!isFlipped)}
        style={{ transformStyle: "preserve-3d", transition: "transform 0.6s" }}
      >
        <div
          className="absolute w-full h-full flex items-center justify-center p-4"
          style={{ backfaceVisibility: "hidden", transform: isFlipped ? "rotateY(180deg)" : "rotateY(0deg)" }}
        >
          <p className="text-xl font-semibold break-words overflow-hidden">{card.front}</p>
        </div>
        <div
          className="absolute w-full h-full flex items-center justify-center bg-secondary rounded-lg p-4"
          style={{ backfaceVisibility: "hidden", transform: isFlipped ? "rotateY(0deg)" : "rotateY(180deg)" }}
        >
          <p className="text-lg break-words overflow-hidden">{card.back}</p>
        </div>
      </div>
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          Card {currentIndex + 1} of {flashcards.length}
        </p>
        <Button onClick={handleNext}>Next Card</Button>
      </div>
    </div>
  )
}

export function QuizPlayer({ quizItems }: { quizItems: Array<{ question: string; options: string[]; answer: string }> }) {
  const [currentIndex, setCurrentIndex] = useState(0)
  const [selectedOption, setSelectedOption] = useState<string | null>(null)
  const [isCorrect, setIsCorrect] = useState<boolean | null>(null)
  const [score, setScore] = useState(0)
  const [showResults, setShowResults] = useState(false)

  const currentQuestion = quizItems[currentIndex]
  
  // Debug: Log quiz data structure
  console.log("Quiz data:", quizItems)
  console.log("Current question:", currentQuestion)

  const handleOptionSelect = (option: string) => {
    if (selectedOption) return
    setSelectedOption(option)
    
    // Check if the selected option matches the answer
    // The answer might be in different formats, so we normalize it
    const normalizedSelected = option.trim().toLowerCase()
    const normalizedAnswer = currentQuestion.answer.trim().toLowerCase()
    const correct = normalizedSelected === normalizedAnswer
    
    setIsCorrect(correct)
    if (correct) {
      setScore((prev) => prev + 1)
    }
  }

  const handleNext = () => {
    if (currentIndex < quizItems.length - 1) {
      setCurrentIndex((prev) => prev + 1)
      setSelectedOption(null)
      setIsCorrect(null)
    } else {
      setShowResults(true)
    }
  }

  const handleRestart = () => {
    setCurrentIndex(0)
    setSelectedOption(null)
    setIsCorrect(null)
    setScore(0)
    setShowResults(false)
  }

  if (!quizItems || quizItems.length === 0) {
    return <p>No quiz available.</p>
  }

  if (showResults) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Quiz Results</CardTitle>
        </CardHeader>
        <CardContent className="text-center space-y-4">
          <p className="text-2xl font-bold">
            You scored {score} out of {quizItems.length}
          </p>
          <p className="text-lg text-muted-foreground">({((score / quizItems.length) * 100).toFixed(0)}%)</p>
          <Button onClick={handleRestart}>Try Again</Button>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>
          Question {currentIndex + 1} of {quizItems.length}
        </CardTitle>
        <p className="text-lg pt-2">{currentQuestion.question}</p>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {currentQuestion.options.map((option, index) => {
            const isSelected = selectedOption === option
            const normalizedOption = option.trim().toLowerCase()
            const normalizedAnswer = currentQuestion.answer.trim().toLowerCase()
            const isAnswer = normalizedOption === normalizedAnswer
            return (
              <Button
                key={index}
                variant="outline"
                className={`h-auto py-3 justify-start text-left whitespace-normal ${
                  isSelected && isCorrect ? "bg-green-100 border-green-500 text-green-800" : ""
                } ${isSelected && !isCorrect ? "bg-red-100 border-red-500 text-red-800" : ""} ${
                  selectedOption && isAnswer && !isSelected ? "bg-green-100 border-green-500 text-green-800" : ""
                }`}
                onClick={() => handleOptionSelect(option)}
                disabled={!!selectedOption}
              >
                <div className="flex items-center w-full">
                  <span className="flex-1">{option}</span>
                  {isSelected && isCorrect && <Check className="h-5 w-5 text-green-600" />}
                  {isSelected && !isCorrect && <X className="h-5 w-5 text-red-600" />}
                  {selectedOption && isAnswer && !isSelected && <Check className="h-5 w-5 text-green-600" />}
                </div>
              </Button>
            )
          })}
        </div>
        {selectedOption && (
          <div className="flex justify-end">
            <Button onClick={handleNext}>
              {currentIndex < quizItems.length - 1 ? "Next Question" : "Finish Quiz"}
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
