"use client"

import type React from "react"

import { useState, useRef } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { FileText, UploadCloud, X } from "lucide-react"

interface UploadCardProps {
  onUpload: (file: File) => void
  isUploading: boolean
}

export function UploadCard({ onUpload, isUploading }: UploadCardProps) {
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [uploadedFile, setUploadedFile] = useState<File | null>(null)

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file && file.type === "application/pdf") {
      setUploadedFile(file)
    } else {
      setUploadedFile(null)
      alert("Please select a PDF file.")
    }
  }

  const handleUploadClick = () => {
    if (uploadedFile) {
      onUpload(uploadedFile)
    } else {
      alert("Please choose a PDF file first.")
    }
  }

  const handleRemoveFile = () => {
    setUploadedFile(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = "" // Clear the input
    }
  }

  return (
    <Card className="p-6 text-center">
      <CardContent className="flex flex-col items-center justify-center p-0">
        {!uploadedFile ? (
          <>
            <Input
              id="pdf-upload"
              type="file"
              accept=".pdf"
              onChange={handleFileChange}
              ref={fileInputRef}
              className="hidden"
            />
            <Button
              onClick={() => fileInputRef.current?.click()}
              disabled={isUploading}
              className="flex items-center gap-2 px-6 py-3 text-lg"
            >
              <UploadCloud className="h-6 w-6" />
              Choose PDF File
            </Button>
            <p className="text-sm text-muted-foreground mt-2">Only PDF files are supported.</p>
          </>
        ) : (
          <div className="flex flex-col items-center gap-4">
            <div className="flex items-center gap-2 text-lg font-medium text-green-600">
              <FileText className="h-6 w-6" />
              <span>{uploadedFile.name}</span>
              <Button
                variant="ghost"
                size="icon"
                onClick={handleRemoveFile}
                className="text-muted-foreground hover:text-destructive"
              >
                <X className="h-4 w-4" />
                <span className="sr-only">Remove file</span>
              </Button>
            </div>
            <p className="text-sm text-muted-foreground">File ready for processing.</p>
            <div className="flex gap-4">
              <Button onClick={handleUploadClick} disabled={isUploading} className="px-6 py-3 text-lg">
                Process PDF
              </Button>
              <Button
                variant="outline"
                onClick={() => fileInputRef.current?.click()}
                disabled={isUploading}
                className="px-6 py-3 text-lg"
              >
                Choose Another PDF
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
