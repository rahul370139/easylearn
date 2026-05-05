"use client"

import type React from "react"
import { learnAPI, chatAPI } from "@/lib/api"
import { useState, useRef, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Separator } from "@/components/ui/separator"
import { Settings, Send, Brain, Sparkles } from "lucide-react"
import { toast } from "@/components/ui/use-toast"
import { useAuth } from "@/components/auth-provider"
import { UnifiedAIInterface } from "@/components/unified-ai-interface"

async function uploadToDistill(file: File, ownerId: string) {
  console.log("uploadToDistill called with:", {
    fileName: file.name,
    fileSize: file.size,
    fileType: file.type,
    ownerId,
  })

  try {
    const data = await learnAPI.distill(file, ownerId)
    console.log("Distill upload successful, response:", data)
    return data
  } catch (error) {
    console.error("Distill upload failed with error:", error)
    throw error
  }
}

async function uploadFileForChat(file: File, userId: string, conversationId: string | null, explanationLevel: string) {
  console.log("uploadFileForChat called with:", { fileName: file.name, userId, conversationId, explanationLevel })

  try {
    const data = await chatAPI.uploadFile(file, userId, conversationId || undefined, explanationLevel)
    console.log("Chat upload success:", data)
    return data as { conversation_id: string; response: string }
  } catch (error) {
    console.error("Chat upload failed with error:", error)
    throw error
  }
}

export default function LearnPage() {
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([])
  const [experienceLevel, setExperienceLevel] = useState("intermediate")
  const [framework, setFramework] = useState("general")
  const [appliedExperienceLevel, setAppliedExperienceLevel] = useState("intermediate")
  const [appliedFramework, setAppliedFramework] = useState("general")
  const [isDragOver, setIsDragOver] = useState(false)
  const [currentLessonId, setCurrentLessonId] = useState<number | null>(null)
  const [conversationId, setConversationId] = useState<string | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const { user } = useAuth()

  // Load persisted conversation_id on mount
  useEffect(() => {
    try {
      const storedConversationId = localStorage.getItem("trainpi_conversation_id")
      if (storedConversationId) {
        setConversationId(storedConversationId)
      }
    } catch {}
  }, [])

  // Persist conversation_id when it changes
  useEffect(() => {
    if (conversationId) {
      try {
        localStorage.setItem("trainpi_conversation_id", conversationId)
      } catch {}
    }
  }, [conversationId])

  const handleApplySettings = () => {
    setAppliedExperienceLevel(experienceLevel)
    setAppliedFramework(framework)
    toast({
      title: "Settings Applied",
      description: `Experience level: ${experienceLevel}, Framework: ${framework}`,
    })
  }

  const handleFileUpload = async (fileList: FileList | null) => {
    if (!fileList || fileList.length === 0) return

    const supportedFiles = Array.from(fileList).filter((file) => file.type === "application/pdf")

    if (supportedFiles.length === 0) {
      toast({
        title: "Invalid file type",
        description: "Please upload PDF files only.",
        variant: "destructive",
      })
      return
    }

    if (supportedFiles.length > 1) {
      toast({
        title: "Multiple files",
        description: "Please upload one file at a time.",
        variant: "destructive",
      })
      return
    }

    setIsUploading(true)

    try {
      const explanationLevel =
        appliedExperienceLevel === "beginner"
          ? "5_year_old"
          : appliedExperienceLevel === "intermediate"
            ? "intern"
            : "senior"

      // Upload to distill for lesson processing
      const distillResp = await uploadToDistill(supportedFiles[0], user?.id || "anonymous-user")
      console.log("Distill response:", distillResp)

      // Upload to chat for conversation context
      const chatUploadResp = await uploadFileForChat(
        supportedFiles[0],
        user?.id || "anonymous-user",
        conversationId,
        explanationLevel,
      )
      console.log("Chat upload response:", chatUploadResp)

      // Ingest distilled content into chat
      if (distillResp.lesson_id && chatUploadResp.conversation_id) {
        try {
          await chatAPI.ingestDistilled(distillResp.lesson_id.toString(), user?.id || "anonymous-user", {
            conversation_id: chatUploadResp.conversation_id,
            explanation_level: explanationLevel,
            framework: appliedFramework,
          })
        } catch (error) {
          console.warn("Error ingesting lesson content:", error)
        }
      }

      // Update state
      setUploadedFiles([supportedFiles[0]])
      setCurrentLessonId(distillResp.lesson_id)
      setConversationId(chatUploadResp.conversation_id)

      toast({
        title: "File Processed Successfully",
        description: `${supportedFiles[0].name} uploaded and ready for AI interaction!`,
      })
    } catch (err) {
      console.error("Upload failed:", err)
      let errorMessage = "Upload failed. Please try again."
      if (err instanceof Error) {
        if (err.message.includes("Failed to process PDF")) {
          errorMessage = "The PDF could not be processed. Please ensure it contains readable text and try again."
        } else if (err.message.includes("PDF only")) {
          errorMessage = "Please upload a valid PDF file."
        } else {
          errorMessage = err.message
        }
      }
      toast({
        title: "Upload failed",
        description: errorMessage,
        variant: "destructive",
      })
    } finally {
      setIsUploading(false)
    }
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
    handleFileUpload(e.dataTransfer.files)
  }

  return (
    <div className="container mx-auto px-4 py-6">
      <div className="space-y-6">
        {/* Header */}
        <div className="text-center space-y-3">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            AI-Powered Learning Hub
          </h1>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Upload your documents and interact with our unified AI assistant for personalized learning experiences.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Main Learning Area */}
          <div className="lg:col-span-3">
            <Card className="shadow-lg bg-background border">
              <CardHeader className="border-b bg-gradient-to-r from-blue-50/50 to-purple-50/50 dark:from-blue-950/10 dark:to-purple-950/10">
                <CardTitle className="flex items-center gap-2">
                  <Brain className="h-5 w-5 text-blue-600" />
                  Unified AI Learning Assistant
                </CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <UnifiedAIInterface
                  files={uploadedFiles}
                  selectedLevel={appliedExperienceLevel}
                  selectedFramework={appliedFramework}
                  currentLessonId={currentLessonId}
                  conversationId={conversationId}
                  onConversationIdChange={setConversationId}
                  onFileUpload={handleFileUpload}
                  isUploading={isUploading}
                  isDragOver={isDragOver}
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDrop}
                  fileInputRef={fileInputRef}
                />
              </CardContent>
            </Card>
          </div>

          {/* Settings Sidebar */}
          <div className="space-y-6">
            <Card className="shadow-lg bg-background border">
              <CardHeader className="pb-4">
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2 text-lg">
                    <Settings className="h-5 w-5" />
                    Learning Settings
                  </CardTitle>
                  <Button
                    size="sm"
                    onClick={handleApplySettings}
                    className="bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 shadow-md"
                  >
                    <Send className="h-4 w-4 mr-1" />
                    Apply
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="experience" className="text-sm font-medium">
                    Experience Level
                  </Label>
                  <Select value={experienceLevel} onValueChange={setExperienceLevel}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select level" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="beginner">Beginner</SelectItem>
                      <SelectItem value="intermediate">Intermediate</SelectItem>
                      <SelectItem value="advanced">Advanced</SelectItem>
                      <SelectItem value="expert">Expert</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="framework" className="text-sm font-medium">
                    Framework/Tool Focus
                  </Label>
                  <Select value={framework} onValueChange={setFramework}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select framework" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="general">General</SelectItem>
                      <SelectItem value="react">React</SelectItem>
                      <SelectItem value="python">Python</SelectItem>
                      <SelectItem value="nodejs">Node.js</SelectItem>
                      <SelectItem value="docker">Docker</SelectItem>
                      <SelectItem value="fastapi">FastAPI</SelectItem>
                      <SelectItem value="machine-learning">Machine Learning</SelectItem>
                      <SelectItem value="data-science">Data Science</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <Separator />

                <div className="space-y-3">
                  <h4 className="text-sm font-medium flex items-center gap-2">
                    <Sparkles className="h-4 w-4" />
                    Current Settings
                  </h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Level:</span>
                      <span className="font-medium">{appliedExperienceLevel}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Framework:</span>
                      <span className="font-medium">{appliedFramework}</span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Learning Tips */}
            <Card className="shadow-lg bg-gradient-to-br from-green-50/80 to-emerald-50/80 dark:from-green-950/20 dark:to-emerald-950/20 dark:bg-card border">
              <CardHeader className="pb-3">
                <CardTitle className="text-lg text-green-700 dark:text-green-400">💡 Learning Tips</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <div className="text-sm space-y-1.5">
                  <p>
                    • <strong>Unified AI:</strong> Chat and agentic features combined
                  </p>
                  <p>
                    • <strong>Quick Actions:</strong> Generate summaries, quizzes, flashcards
                  </p>
                  <p>
                    • <strong>Progress Tracking:</strong> Monitor your learning journey
                  </p>
                  <p>• Upload PDFs for personalized learning</p>
                  <p>• Adjust settings for optimal experience</p>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}
