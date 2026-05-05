"use client"

import { Button } from "@/components/ui/button"
import { ChevronLeft, ChevronRight } from "lucide-react"

interface CareerStepperProps {
  currentStep: number
  totalSteps: number
  onNext: () => void
  onPrevious: () => void
  canGoNext: boolean
}

export function CareerStepper({ currentStep, totalSteps, onNext, onPrevious, canGoNext }: CareerStepperProps) {
  return (
    <div className="flex items-center justify-between">
      <Button
        variant="outline"
        onClick={onPrevious}
        disabled={currentStep === 1}
        className="flex items-center gap-2 bg-transparent"
      >
        <ChevronLeft className="h-4 w-4" />
        Previous
      </Button>

      <div className="flex items-center gap-2">
        {Array.from({ length: totalSteps }, (_, i) => (
          <div
            key={i}
            className={`h-2 w-8 rounded-full transition-colors ${i + 1 <= currentStep ? "bg-primary" : "bg-muted"}`}
          />
        ))}
      </div>

      <Button onClick={onNext} disabled={!canGoNext} className="flex items-center gap-2">
        {currentStep === totalSteps ? "Get Results" : "Next"}
        <ChevronRight className="h-4 w-4" />
      </Button>
    </div>
  )
}
