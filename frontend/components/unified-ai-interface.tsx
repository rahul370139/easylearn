"use client"

import type React from "react"

import { useState, useRef, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { useAuth } from "@/components/auth-provider"
import { chatAPI, agenticAPI } from "@/lib/api"

const SUPPORTED_TYPES = new Set([
  "text",
  "lesson",
  "summary",
  "flashcards",
  "quiz",
  "workflow",
  "diagnostic",
  "progress",
])
import { toast } from "@/components/ui/use-toast"
import {
  FlashcardsComponent,
  QuizComponent,
  SummaryComponent,
  WorkflowComponent,
  LessonComponent,
  DiagnosticComponent,
} from "@/components/result-components"
import {
  Send,
  Bot,
  User,
  Paperclip,
  X,
  FileText,
  BookOpen,
  Target,
  HelpCircle,
  Zap,
  BarChart3,
  TrendingUp,
  Upload,
} from "lucide-react"

interface Message {
  id: string
  content: string
  sender: "user" | "ai"
  timestamp: Date
  files?: File[]
  type?: "text" | "lesson" | "summary" | "flashcards" | "quiz" | "workflow" | "progress" | "diagnostic"
  lessonData?: any
  summaryData?: any
  flashcardData?: Array<{ front: string; back: string }>
  quizData?: Array<{ question: string; options: string[]; answer: string }>
  workflowData?: any
  keyPoints?: string[]
  sessionId?: string
  pdfId?: string
  userId?: string
  topic?: string
}

interface MasteryData {
  status: string
  mastery: {
    overall_score: number
    topic_scores: Record<string, number>
    skill_breakdown: Record<string, number>
    learning_progress: any
    recommended_topics: string[]
  }
}

interface UnifiedAIInterfaceProps {
  files: File[]
  selectedLevel: string
  selectedFramework: string
  currentLessonId?: number | null
  conversationId?: string | null
  onConversationIdChange?: (id: string) => void
  onFileUpload?: (files: FileList | null) => void
  isUploading?: boolean
  isDragOver?: boolean
  onDragOver?: (e: React.DragEvent) => void
  onDragLeave?: (e: React.DragEvent) => void
  onDrop?: (e: React.DragEvent) => void
  fileInputRef?: React.RefObject<HTMLInputElement>
}

export function UnifiedAIInterface({
  files,
  selectedLevel,
  selectedFramework,
  currentLessonId,
  conversationId,
  onConversationIdChange,
  onFileUpload,
  isUploading = false,
  isDragOver = false,
  onDragOver,
  onDragLeave,
  onDrop,
  fileInputRef,
}: UnifiedAIInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [inputMessage, setInputMessage] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([])
  const [masteryData, setMasteryData] = useState<MasteryData | null>(null)
  const [uploadedPdfId, setUploadedPdfId] = useState<string | null>(null)
  const scrollAreaRef = useRef<HTMLDivElement>(null)
  const internalFileInputRef = useRef<HTMLInputElement>(null)
  const { user } = useAuth()

  const quickActions = [
    {
      id: "summary",
      label: "Summary",
      icon: FileText,
      prompt: "Generate a comprehensive summary of the uploaded document with key points",
      description: "Get a concise overview",
      color: "bg-blue-500 hover:bg-blue-600 text-white",
    },
    {
      id: "lesson",
      label: "Lesson",
      icon: BookOpen,
      prompt: "Create a structured lesson plan from this content with learning objectives",
      description: "Generate structured learning",
      color: "bg-green-500 hover:bg-green-600 text-white",
    },
    {
      id: "diagnostic",
      label: "Diagnostic",
      icon: Target,
      prompt: "Run a diagnostic assessment to test my knowledge on this material",
      description: "Test your knowledge",
      color: "bg-orange-500 hover:bg-orange-600 text-white",
    },
    {
      id: "quiz",
      label: "Quiz",
      icon: HelpCircle,
      prompt: "Generate an interactive quiz with multiple choice questions from the uploaded document",
      description: "Practice with questions",
      color: "bg-purple-500 hover:bg-purple-600 text-white",
    },
    {
      id: "flashcards",
      label: "Flashcards",
      icon: Zap,
      prompt: "Create interactive flashcards for key concepts from the document",
      description: "Quick review cards",
      color: "bg-yellow-500 hover:bg-yellow-600 text-white",
    },
    {
      id: "workflow",
      label: "Workflow",
      icon: BarChart3,
      prompt: "Create a learning workflow diagram from this content",
      description: "Step-by-step process",
      color: "bg-indigo-500 hover:bg-indigo-600 text-white",
    },
  ]

  useEffect(() => {
    setUploadedFiles(files)
  }, [files])

  useEffect(() => {
    loadMasteryData()
  }, [user])

  const loadMasteryData = async () => {
    if (!user?.id) {
      setMasteryData({
        status: "success",
        mastery: {
          overall_score: 0,
          topic_scores: {},
          skill_breakdown: {},
          learning_progress: {},
          recommended_topics: ["Sign in to track your learning progress"],
        },
      })
      return
    }

    try {
      const data = await agenticAPI.getMastery(user.id)
      setMasteryData(data)
    } catch (error) {
      console.error("Failed to load mastery data:", error)
      setMasteryData({
        status: "success",
        mastery: {
          overall_score: 0,
          topic_scores: {},
          skill_breakdown: {},
          learning_progress: {},
          recommended_topics: ["Unable to load progress data. Please try again later."],
        },
      })
    }
  }

  const scrollToBottom = () => {
    if (scrollAreaRef.current) {
      const scrollContainer = scrollAreaRef.current.querySelector("[data-radix-scroll-area-viewport]")
      if (scrollContainer) {
        scrollContainer.scrollTop = scrollContainer.scrollHeight
      }
    }
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const parseAPIResponse = (data: any): Partial<Message> => {
    const messageData: Partial<Message> = {
      content: data.response || "I'm here to help you learn!",
      type: "text",
      sessionId: data.session_id,
      pdfId: uploadedPdfId || undefined,
      userId: user?.id || undefined,
    }

    // Trust the backend `type` first. Backend handlers in distiller.py set this explicitly
    // for lesson/quiz/flashcards/workflow/summary/diagnostic. Fall back to keyword sniff
    // only when no explicit type came through (e.g. plain chat that returned quiz-like text).
    const explicitType = typeof data.type === "string" ? data.type : ""

    if (explicitType === "quiz" || explicitType === "diagnostic") {
      const questions =
        (Array.isArray(data.quiz) && data.quiz) ||
        (Array.isArray(data.questions) && data.questions) ||
        (data.quiz_data && Array.isArray(data.quiz_data.questions) && data.quiz_data.questions) ||
        parseQuizFromText(data.response || "")
      messageData.type = explicitType as Message["type"]
      messageData.quizData = questions
      return messageData
    }

    if (explicitType === "flashcards") {
      const cards =
        (Array.isArray(data.flashcards) && data.flashcards) ||
        (data.flashcard_data && Array.isArray(data.flashcard_data.cards) && data.flashcard_data.cards) ||
        parseFlashcardsFromText(data.response || "")
      messageData.type = "flashcards"
      messageData.flashcardData = cards
      return messageData
    }

    if (explicitType === "summary") {
      messageData.type = "summary"
      const sd = data.summary_data
      if (sd && typeof sd === "object") {
        const title = sd.title ? `**${sd.title}**\n\n` : ""
        const overview = sd.overview ? `${sd.overview}` : ""
        messageData.summaryData = (title + overview).trim() || data.response || ""
        messageData.keyPoints = Array.isArray(sd.key_points) ? sd.key_points : []
      } else {
        messageData.summaryData = data.summary || data.response || ""
        messageData.keyPoints = Array.isArray(data.key_points)
          ? data.key_points
          : parseKeyPointsFromText(data.response || "")
      }
      return messageData
    }

    if (explicitType === "workflow") {
      messageData.type = "workflow"
      // Pass the structured workflow_data straight through so WorkflowComponent
      // can render rich fields (inputs/outputs/tools/pitfalls/branches/mermaid).
      // Falls back to the raw response text if the backend gave us nothing
      // structured.
      messageData.workflowData = data.workflow_data || data.workflow || data.response || ""
      return messageData
    }

    if (explicitType === "lesson") {
      messageData.type = "lesson"
      messageData.lessonData = data.lesson_data || data.lesson || data.content || data.response
      return messageData
    }

    // Lightweight fallback heuristics for plain chat responses that *look* structured.
    if (Array.isArray(data.questions) && data.questions.length) {
      messageData.type = "quiz"
      messageData.quizData = data.questions
      return messageData
    }
    if (Array.isArray(data.flashcards) && data.flashcards.length) {
      messageData.type = "flashcards"
      messageData.flashcardData = data.flashcards
      return messageData
    }

    return messageData
  }

  const parseQuizFromText = (text: string): Array<{ question: string; options: string[]; answer: string }> => {
    const questions: Array<{ question: string; options: string[]; answer: string }> = []
    const lines = text.split("\n").filter((line) => line.trim())

    let currentQuestion = ""
    let currentOptions: string[] = []
    let currentAnswer = ""

    for (const line of lines) {
      // Match various question patterns - enhanced for diagnostic format
      if (line.match(/^\d+\.|Question \d+:|Q\d+:|^\d+\)|^\*\*\d+\./)) {
        // Save previous question if exists
        if (currentQuestion && currentOptions.length > 0) {
          questions.push({
            question: currentQuestion,
            options: currentOptions,
            answer: currentAnswer || currentOptions[0],
          })
        }
        // Start new question - clean up markdown formatting
        currentQuestion = line.replace(/^\d+\.|Question \d+:|Q\d+:|^\d+\)|^\*\*\d+\.|\*\*/g, "").trim()
        currentOptions = []
        currentAnswer = ""
      } else if (line.match(/^[A-Z]\)|^[a-z]\)/)) {
        // Handle options A, B, C, D, E, F, etc. (both uppercase and lowercase)
        const optionText = line.replace(/^[A-Za-z]\)\s*/, "").trim()
        if (optionText) {
          currentOptions.push(optionText)
        }
      } else if (line.includes("Answer:") || line.includes("Correct:") || line.includes("Answer is:") || line.includes("**Answer:**")) {
        currentAnswer = line.replace(/Answer:|Correct:|Answer is:|\*\*Answer:\*\*/g, "").trim()
      } else if (currentQuestion && !currentAnswer && line.trim() && !line.match(/^[A-Za-z]\)/) && !line.includes("Section") && !line.includes("**Section")) {
        // If we have a question but no options yet, this might be part of the question
        // Skip section headers, instructional text, and other non-question content
        if (!line.includes("Multiple Choice") && 
            !line.includes("Short Answer") && 
            !line.includes("Diagnostic Assessment") &&
            !line.includes("Choose your answer") &&
            !line.includes("Please respond with") &&
            !line.includes("Your Score") &&
            !line.includes("Scoring") &&
            !line.includes("Total Score") &&
            !line.includes("reveal the answers") &&
            !line.includes("provide feedback") &&
            !line.includes("submit your answers") &&
            !line.includes("respond with the following format") &&
            !line.includes("**Choose your answer:**") &&
            !line.includes("**Please respond with**") &&
            !line.includes("**Your Score:**") &&
            !line.includes("**Scoring:**") &&
            !line.includes("**Total Score:**") &&
            !line.includes("**Note:**") &&
            !line.includes("**Let me know**") &&
            !line.includes("**Please respond with the following format:**")) {
          currentQuestion += " " + line.trim()
        }
      }
    }

    // Add last question
    if (currentQuestion && currentOptions.length > 0) {
      questions.push({
        question: currentQuestion,
        options: currentOptions,
        answer: currentAnswer || currentOptions[0],
      })
    }

    // Clean up questions to remove any remaining instructional text
    const cleanedQuestions = questions.map(q => ({
      ...q,
      question: q.question
        .replace(/\*\*Choose your answer:\*\*.*$/g, '')
        .replace(/\*\*Please respond with.*$/g, '')
        .replace(/\*\*Your Score:\*\*.*$/g, '')
        .replace(/\*\*Scoring:\*\*.*$/g, '')
        .replace(/\*\*Total Score:\*\*.*$/g, '')
        .replace(/\*\*Note:\*\*.*$/g, '')
        .replace(/\*\*Let me know.*$/g, '')
        .replace(/\*\*Please respond with the following format:\*\*.*$/g, '')
        .replace(/Choose your answer:.*$/g, '')
        .replace(/Please respond with.*$/g, '')
        .replace(/Your Score:.*$/g, '')
        .replace(/Scoring:.*$/g, '')
        .replace(/Total Score:.*$/g, '')
        .replace(/Note:.*$/g, '')
        .replace(/Let me know.*$/g, '')
        .replace(/Please respond with the following format:.*$/g, '')
        .replace(/\s+/g, ' ')
        .trim()
    }))

    console.log(`Parsed ${cleanedQuestions.length} questions from text`)
    console.log("Parsed questions:", cleanedQuestions)
    return cleanedQuestions
  }

  const parseFlashcardsFromText = (text: string): Array<{ front: string; back: string }> => {
    const flashcards: Array<{ front: string; back: string }> = []
    const lines = text.split("\n").filter((line) => line.trim())

    let currentFront = ""
    let currentBack = ""

    for (const line of lines) {
      if (line.includes("Front:") || line.includes("Card")) {
        if (currentFront && currentBack) {
          flashcards.push({ front: currentFront, back: currentBack })
        }
        currentFront = line.replace(/Front:|Card \d+:/, "").trim()
        currentBack = ""
      } else if (line.includes("Back:")) {
        currentBack = line.replace(/Back:/, "").trim()
      } else if (currentFront && !currentBack && line.trim()) {
        currentBack = line.trim()
      }
    }

    if (currentFront && currentBack) {
      flashcards.push({ front: currentFront, back: currentBack })
    }

    return flashcards
  }

  const parseKeyPointsFromText = (text: string): string[] => {
    const keyPoints: string[] = []
    const lines = text.split("\n").filter((line) => line.trim())

    // First, try to find explicit key points sections
    let inKeyPointsSection = false
    for (const line of lines) {
      const lowerLine = line.toLowerCase()
      
      // Look for key points section headers
      if (lowerLine.includes("key points") || 
          lowerLine.includes("key takeaways") || 
          lowerLine.includes("main points") ||
          lowerLine.includes("important points") ||
          lowerLine.includes("insights") ||
          lowerLine.includes("action items")) {
        inKeyPointsSection = true
        continue
      }
      
      // If we're in a key points section, look for bullet points
      if (inKeyPointsSection) {
        if (line.match(/^[-•*]\s/) || 
            line.match(/^\d+\.\s/) || 
            line.match(/^[a-zA-Z]\.\s/) ||
            line.match(/^→\s/) ||
            line.match(/^▶\s/) ||
            line.match(/^▪\s/) ||
            line.match(/^▫\s/)) {
          const cleaned = line.replace(/^[-•*→▶▪▫]\s|\d+\.\s|[a-zA-Z]\.\s/, "").trim()
          if (cleaned.length > 15 && cleaned.length < 200) { // Filter for meaningful length
            keyPoints.push(cleaned)
          }
        } else if (line.trim() === "" || line.match(/^[A-Z][^:]*:$/)) {
          // End of key points section
          inKeyPointsSection = false
        }
      }
    }

    // If no structured key points found, try to extract meaningful insights
    if (keyPoints.length === 0) {
      const sentences = text.split(/[.!?]+/).filter(s => {
        const trimmed = s.trim()
        return trimmed.length > 20 && trimmed.length < 150 && 
               (trimmed.includes("important") || 
                trimmed.includes("key") || 
                trimmed.includes("main") || 
                trimmed.includes("should") || 
                trimmed.includes("must") || 
                trimmed.includes("critical") ||
                trimmed.includes("essential") ||
                trimmed.includes("note") ||
                trimmed.includes("remember"))
      })
      
      keyPoints.push(...sentences.slice(0, 5).map(s => s.trim()))
    }

    // If still no key points, extract the most important sentences
    if (keyPoints.length === 0) {
      const sentences = text.split(/[.!?]+/).filter(s => s.trim().length > 30)
      keyPoints.push(...sentences.slice(0, 3).map(s => s.trim()))
    }

    return keyPoints.slice(0, 5) // Limit to 5 most important points
  }


  const handleSendMessage = async () => {
    if (!inputMessage.trim() && uploadedFiles.length === 0) return

    const userMessage: Message = {
      id: Date.now().toString(),
      content: inputMessage,
      sender: "user",
      timestamp: new Date(),
      files: uploadedFiles.length > 0 ? [...uploadedFiles] : undefined,
    }

    setMessages((prev) => [...prev, userMessage])
    const currentMessage = inputMessage
    setInputMessage("")

    if (uploadedFiles.length > 0) {
      try {
        const file = uploadedFiles[0]
        const uploadResponse = await chatAPI.uploadFile(
          file,
          user?.id || "anonymous-user",
          conversationId || undefined,
          selectedLevel === "beginner" ? "5_year_old" : selectedLevel === "intermediate" ? "intern" : "senior",
        )

        // Backend returns `lesson_id` (from supabase_helper.insert_lesson). Older shape used `pdf_id`.
        // We accept either as the document identifier so mastery / diagnostic results can be tied to it.
        const docId = uploadResponse.pdf_id || uploadResponse.lesson_id
        if (docId) {
          setUploadedPdfId(String(docId))
        }

        setUploadedFiles([])
      } catch (error) {
        console.error("File upload failed:", error)
        toast({
          title: "Upload Error",
          description: "Failed to upload file. Please try again.",
          variant: "destructive",
        })
      }
    }

    setIsLoading(true)

    try {
      const data = await chatAPI.sendMessage({
        message: currentMessage,
        user_id: user?.id || "anonymous-user",
        explanation_level:
          selectedLevel === "beginner" ? "5_year_old" : selectedLevel === "intermediate" ? "intern" : "senior",
        conversation_id: conversationId || undefined,
        pdf_id: uploadedPdfId || undefined,
      })

      if (data.conversation_id && onConversationIdChange) {
        onConversationIdChange(data.conversation_id)
      }

      const parsedData = parseAPIResponse(data)

      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: parsedData.content || "Response received",
        sender: "ai",
        timestamp: new Date(),
        ...parsedData,
      }

      setMessages((prev) => [...prev, aiMessage])
    } catch (error) {
      console.error("Error sending message:", error)
      toast({
        title: "Error",
        description: "Failed to send message. Please try again.",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleQuickAction = async (action: (typeof quickActions)[0]) => {
    // Single path: send the action prompt straight through the chat API.
    // The backend (`process_chat_message` in distiller.py) detects the intent
    // (summary / lesson / quiz / flashcards / workflow / diagnostic), runs RAG
    // over the uploaded PDF chunks, and returns a typed payload.
    const userMessage: Message = {
      id: Date.now().toString(),
      content: action.prompt,
      sender: "user",
      timestamp: new Date(),
    }
    setMessages((prev) => [...prev, userMessage])
    setIsLoading(true)

    try {
      const data = await chatAPI.sendMessage({
        message: action.prompt,
        user_id: user?.id || "anonymous-user",
        explanation_level:
          selectedLevel === "beginner" ? "5_year_old" : selectedLevel === "intermediate" ? "intern" : "senior",
        conversation_id: conversationId || undefined,
      })

      if (data.conversation_id && onConversationIdChange) {
        onConversationIdChange(data.conversation_id)
      }

      const parsedData = parseAPIResponse(data)
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: parsedData.content || "Response received",
        sender: "ai",
        timestamp: new Date(),
        ...parsedData,
      }
      setMessages((prev) => [...prev, aiMessage])
    } catch (error) {
      console.error(`Error generating ${action.label}:`, error)
      toast({
        title: "Error",
        description: `Failed to generate ${action.label.toLowerCase()}. Please try again.`,
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files) {
      const newFiles = Array.from(files).filter(
        (file) => file.type === "application/pdf" || file.type === "text/plain" || file.name.endsWith(".md"),
      )
      setUploadedFiles((prev) => [...prev, ...newFiles])
      onFileUpload?.(files)
    }
  }

  const removeUploadedFile = (index: number) => {
    setUploadedFiles((prev) => prev.filter((_, i) => i !== index))
  }

  const renderProgressOverview = () => {
    if (!masteryData || !masteryData.mastery || !masteryData.mastery.topic_scores || Object.keys(masteryData.mastery.topic_scores).length === 0) return null

    return (
      <Card className="mb-4 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-950/20 dark:to-purple-950/20">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-sm">
            <TrendingUp className="h-4 w-4" />
            Learning Progress
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex justify-between text-xs">
            <span>Overall Progress</span>
            <span>{masteryData.mastery.overall_score || 0}%</span>
          </div>
          <Progress value={masteryData.mastery.overall_score || 0} className="h-1" />

          {Object.entries(masteryData.mastery.topic_scores)
            .slice(0, 3)
            .map(([topic, score], index) => (
              <div key={index} className="flex justify-between items-center text-xs">
                <span className="truncate flex-1">{topic}</span>
                <Badge variant="outline" className="ml-2 text-xs">
                  {score || 0}%
                </Badge>
              </div>
            ))}
        </CardContent>
      </Card>
    )
  }

  const renderSpecialContent = (message: Message) => {
    console.log("renderSpecialContent - message type:", message.type, message)
    
    if (message.type === "flashcards" && message.flashcardData && message.flashcardData.length > 0) {
      return (
        <div className="mt-4">
          <FlashcardsComponent
            flashcards={message.flashcardData}
            onAction={(action) => {
              if (action === "download") {
                toast({ title: "Download started", description: "Flashcards are being prepared for download." })
              }
            }}
          />
        </div>
      )
    }

    if (message.type === "quiz" && message.quizData && message.quizData.length > 0) {
      return (
        <div className="mt-4">
          <QuizComponent
            questions={message.quizData}
            onAction={(action) => {
              if (action === "download") {
                toast({ title: "Download started", description: "Quiz results are being prepared for download." })
              }
            }}
            pdfId={message.pdfId}
            userId={message.userId}
            topic={message.topic}
            sessionId={message.sessionId}
            isDiagnostic={false}
          />
        </div>
      )
    }

    if (message.type === "summary" && (message.summaryData || message.content)) {
      return (
        <div className="mt-4">
          <SummaryComponent
            summary={message.summaryData || message.content}
            keyPoints={message.keyPoints}
            onAction={(action) => {
              if (action === "copy") {
                navigator.clipboard.writeText(message.summaryData || message.content)
                toast({ title: "Copied", description: "Summary copied to clipboard." })
              }
            }}
          />
        </div>
      )
    }

    if (message.type === "workflow" && message.workflowData) {
      return (
        <div className="mt-4">
          <WorkflowComponent
            workflow={message.workflowData}
            onAction={(action) => {
              if (action === "copy") {
                const workflowText =
                  typeof message.workflowData === "string"
                    ? message.workflowData
                    : JSON.stringify(message.workflowData, null, 2)
                navigator.clipboard.writeText(workflowText)
                toast({ title: "Copied", description: "Workflow copied to clipboard." })
              }
            }}
          />
        </div>
      )
    }

    if (message.type === "lesson" && message.lessonData) {
      return (
        <div className="mt-4">
          <LessonComponent
            lesson={message.lessonData}
            onAction={(action) => {
              if (action === "copy") {
                const lessonText =
                  typeof message.lessonData === "string"
                    ? message.lessonData
                    : JSON.stringify(message.lessonData, null, 2)
                navigator.clipboard.writeText(lessonText)
                toast({ title: "Copied", description: "Lesson content copied to clipboard." })
              }
            }}
          />
        </div>
      )
    }

    if (message.type === "diagnostic") {
      const diagnosticQuestions = message.quizData || []
      if (!diagnosticQuestions.length) {
        return (
          <div className="mt-4 text-sm text-muted-foreground">
            I couldn't build a grounded diagnostic from this document. Please try again, or upload a clearer PDF.
          </div>
        )
      }
      return (
        <div className="mt-4">
          <DiagnosticComponent
            questions={diagnosticQuestions}
            onAction={(action) => {
              if (action === "download") {
                toast({ title: "Download started", description: "Diagnostic results are being prepared for download." })
              }
            }}
            pdfId={message.pdfId}
            userId={message.userId}
            topic={message.topic}
            sessionId={message.sessionId}
          />
        </div>
      )
    }

    return null
  }

  return (
    <div className="flex flex-col h-[600px] border rounded-lg bg-background">
      {masteryData && masteryData.mastery && masteryData.mastery.topic_scores && Object.keys(masteryData.mastery.topic_scores).length > 0 && (
        <div className="p-4 border-b shrink-0">{renderProgressOverview()}</div>
      )}

      {files.length === 0 ? (
        <div className="flex-1 p-8">
          <div
            className={`border-2 border-dashed rounded-lg p-8 text-center transition-all duration-300 bg-background/50 ${
              isDragOver
                ? "border-primary bg-primary/5 scale-105"
                : "border-muted-foreground/25 hover:border-primary/50 hover:bg-accent/30"
            }`}
            onDragOver={onDragOver}
            onDragLeave={onDragLeave}
            onDrop={onDrop}
          >
            <div className="space-y-4">
              <div className="w-16 h-16 mx-auto bg-gradient-to-r from-blue-500 to-purple-500 rounded-full flex items-center justify-center">
                <Upload className="h-8 w-8 text-white" />
              </div>
              <div>
                <p className="text-xl font-medium">Drop your files here</p>
                <p className="text-muted-foreground">or click to browse</p>
              </div>
              <Input
                ref={internalFileInputRef}
                type="file"
                multiple
                accept=".pdf"
                onChange={handleFileUpload}
                className="hidden"
                id="file-upload"
              />
              <Label htmlFor="file-upload">
                <Button variant="outline" className="cursor-pointer bg-transparent" asChild disabled={isUploading}>
                  <span>{isUploading ? "Processing..." : "Choose Files"}</span>
                </Button>
              </Label>
              <p className="text-sm text-muted-foreground">Supports PDF files only</p>
            </div>
          </div>

          <div className="mt-6 border-t pt-6">
            <div className="text-center mb-4">
              <Bot className="h-8 w-8 mx-auto text-muted-foreground mb-2" />
              <p className="text-sm text-muted-foreground">
                You can also chat with me directly! Ask questions about learning, get study tips, or upload a document
                for personalized assistance.
              </p>
            </div>

            <div className="mb-4">
              <div className="flex flex-wrap gap-2 justify-center mb-3">
                {quickActions.map((action) => {
                  const Icon = action.icon
                  return (
                    <Button
                      key={action.id}
                      variant="outline"
                      size="sm"
                      className="h-8 px-3 flex items-center gap-1 text-xs hover:bg-primary hover:text-primary-foreground transition-all duration-200 bg-transparent"
                      onClick={() => handleQuickAction(action)}
                      disabled={isLoading}
                    >
                      <Icon className="h-3 w-3" />
                      {action.label}
                    </Button>
                  )
                })}
              </div>
              <p className="text-xs text-muted-foreground text-center">
                Upload a PDF to fully activate AI learning tools
              </p>
            </div>

            <div className="flex gap-2">
              <Button variant="outline" size="icon" onClick={handleSendMessage} className="shrink-0 bg-transparent">
                <Paperclip className="h-4 w-4" />
              </Button>
              <Input
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask me anything about learning..."
                className="flex-1"
                disabled={isLoading}
              />
              <Button
                onClick={handleSendMessage}
                disabled={isLoading || (!inputMessage.trim() && uploadedFiles.length === 0)}
                className="shrink-0"
              >
                <Send className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      ) : (
        <>
          <ScrollArea ref={scrollAreaRef} className="flex-1 min-h-0">
            <div className="p-4 space-y-4">
              {messages.length === 0 && (
                <div className="text-center py-8">
                  <Bot className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                  <p className="text-muted-foreground mb-4">
                    Hello! I'm your unified AI learning assistant. Upload files and ask questions or use quick actions
                    to get started.
                  </p>
                  <div className="flex flex-wrap gap-2 justify-center">
                    <Badge variant="outline">Level: {selectedLevel}</Badge>
                    <Badge variant="outline">Focus: {selectedFramework}</Badge>
                  </div>
                </div>
              )}

              {messages.map((message) => (
                <div key={message.id} className={`flex gap-3 ${message.sender === "user" ? "justify-end" : ""}`}>
                  {message.sender === "ai" && (
                    <Avatar className="h-8 w-8 shrink-0">
                      <AvatarFallback className="bg-blue-100 text-blue-600">
                        <Bot className="h-4 w-4" />
                      </AvatarFallback>
                    </Avatar>
                  )}

                  <div
                    className={`max-w-[80%] rounded-lg p-3 ${
                      message.sender === "user"
                        ? "bg-primary text-primary-foreground ml-auto"
                        : "bg-muted text-muted-foreground"
                    }`}
                  >
                    {!renderSpecialContent(message) && (
                      <p className="text-sm whitespace-pre-wrap break-words">{message.content}</p>
                    )}

                    {message.files && message.files.length > 0 && (
                      <div className="mt-2 space-y-1">
                        {message.files.map((file, index) => (
                          <div key={index} className="flex items-center gap-2 text-xs opacity-75">
                            <Paperclip className="h-3 w-3" />
                            <span className="truncate">{file.name}</span>
                          </div>
                        ))}
                      </div>
                    )}

                    {renderSpecialContent(message)}

                    <div className="text-xs opacity-50 mt-1">
                      {message.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                    </div>
                  </div>

                  {message.sender === "user" && (
                    <Avatar className="h-8 w-8 shrink-0">
                      <AvatarFallback className="bg-green-100 text-green-600">
                        <User className="h-4 w-4" />
                      </AvatarFallback>
                    </Avatar>
                  )}
                </div>
              ))}

              {isLoading && (
                <div className="flex gap-3">
                  <Avatar className="h-8 w-8 shrink-0">
                    <AvatarFallback className="bg-blue-100 text-blue-600">
                      <Bot className="h-4 w-4" />
                    </AvatarFallback>
                  </Avatar>
                  <div className="bg-muted rounded-lg p-3">
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-current rounded-full animate-bounce" />
                      <div
                        className="w-2 h-2 bg-current rounded-full animate-bounce"
                        style={{ animationDelay: "0.1s" }}
                      />
                      <div
                        className="w-2 h-2 bg-current rounded-full animate-bounce"
                        style={{ animationDelay: "0.2s" }}
                      />
                    </div>
                  </div>
                </div>
              )}
            </div>
          </ScrollArea>

          {uploadedFiles.length > 0 && (
            <div className="border-t p-3 bg-muted/30 shrink-0">
              <div className="flex flex-wrap gap-2">
                {uploadedFiles.map((file, index) => (
                  <div key={index} className="flex items-center gap-2 bg-background rounded px-2 py-1 text-sm">
                    <Paperclip className="h-3 w-3" />
                    <span className="truncate max-w-32">{file.name}</span>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => removeUploadedFile(index)}
                      className="h-4 w-4 p-0 hover:bg-red-100"
                    >
                      <X className="h-3 w-3" />
                    </Button>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="border-t p-3 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-950/20 dark:to-purple-950/20 shrink-0">
            <div className="flex flex-wrap gap-2 justify-center mb-3">
              {quickActions.map((action) => {
                const Icon = action.icon
                return (
                  <Button
                    key={action.id}
                    variant="outline"
                    size="sm"
                    className="h-8 px-3 flex items-center gap-1 text-xs hover:bg-primary hover:text-primary-foreground transition-all duration-200 bg-transparent"
                    onClick={() => handleQuickAction(action)}
                    disabled={isLoading}
                  >
                    <Icon className="h-3 w-3" />
                    {action.label}
                  </Button>
                )
              })}
            </div>
            {!uploadedPdfId && (
              <p className="text-xs text-muted-foreground text-center">
                Upload a PDF to fully activate AI learning tools
              </p>
            )}
          </div>

          <div className="border-t p-4 shrink-0">
            <div className="flex gap-2">
              <input
                ref={internalFileInputRef}
                type="file"
                multiple
                accept=".pdf,.txt,.md"
                onChange={handleFileUpload}
                className="hidden"
              />
              <Button
                variant="outline"
                size="icon"
                onClick={() => internalFileInputRef?.current?.click()}
                className="shrink-0"
              >
                <Paperclip className="h-4 w-4" />
              </Button>
              <Input
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask me anything about your learning materials..."
                className="flex-1"
                disabled={isLoading}
              />
              <Button
                onClick={handleSendMessage}
                disabled={isLoading || (!inputMessage.trim() && uploadedFiles.length === 0)}
                className="shrink-0"
              >
                <Send className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
