"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Clock, BookOpen, Brain } from "lucide-react"
import { useState } from "react"

interface LessonCardProps {
  lesson: {
    id: string
    title: string
    summary: string[]
    estimatedTime: string
  }
}

export function LessonCard({ lesson }: LessonCardProps) {
  const [mode, setMode] = useState<"flashcards" | "quiz">("flashcards")

  return (
    <Card className="group hover:shadow-lg transition-all duration-300 hover:-translate-y-1">
      <CardHeader>
        <div className="flex items-start justify-between">
          <CardTitle className="text-lg group-hover:text-primary transition-colors">{lesson.title}</CardTitle>
          <Badge variant="secondary" className="flex items-center gap-1">
            <Clock className="h-3 w-3" />
            {lesson.estimatedTime}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <ul className="space-y-2">
          {lesson.summary.map((point, index) => (
            <li key={index} className="flex items-start gap-2 text-sm text-muted-foreground">
              <span className="w-1.5 h-1.5 bg-primary rounded-full mt-2 flex-shrink-0" />
              {point}
            </li>
          ))}
        </ul>

        <div className="flex items-center gap-2 pt-2">
          <Button
            variant={mode === "flashcards" ? "default" : "outline"}
            size="sm"
            onClick={() => setMode("flashcards")}
            className="flex-1"
          >
            <BookOpen className="h-4 w-4 mr-1" />
            Flashcards
          </Button>
          <Button
            variant={mode === "quiz" ? "default" : "outline"}
            size="sm"
            onClick={() => setMode("quiz")}
            className="flex-1"
          >
            <Brain className="h-4 w-4 mr-1" />
            Quiz
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
