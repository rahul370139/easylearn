import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { CheckCircle, Clock, BookOpen } from "lucide-react"

interface RoadmapStep {
  id: number
  title: string
  description: string
  duration: string
  difficulty: string
  skills: string[]
  resources?: string[]
  completed?: boolean
}

interface RoadmapTimelineProps {
  steps: RoadmapStep[]
}

export function RoadmapTimeline({ steps }: RoadmapTimelineProps) {
  return (
    <div className="space-y-6">
      {steps.map((step, index) => (
        <div key={step.id} className="relative">
          {/* Timeline line */}
          {index < steps.length - 1 && <div className="absolute left-6 top-16 h-16 w-0.5 bg-border" />}

          <div className="flex gap-4">
            {/* Timeline dot */}
            <div className="flex-shrink-0">
              <div
                className={`flex h-12 w-12 items-center justify-center rounded-full border-2 ${
                  step.completed
                    ? "bg-green-100 border-green-500 text-green-600"
                    : "bg-background border-border text-muted-foreground"
                }`}
              >
                {step.completed ? (
                  <CheckCircle className="h-6 w-6" />
                ) : (
                  <span className="text-sm font-semibold">{index + 1}</span>
                )}
              </div>
            </div>

            {/* Content */}
            <Card className="flex-1">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle className="text-lg">{step.title}</CardTitle>
                    <p className="text-sm text-muted-foreground mt-1">{step.description}</p>
                  </div>
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Clock className="h-4 w-4" />
                    {step.duration}
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center gap-2">
                  <Badge
                    variant={
                      step.difficulty === "Beginner"
                        ? "secondary"
                        : step.difficulty === "Intermediate"
                          ? "default"
                          : "destructive"
                    }
                  >
                    {step.difficulty}
                  </Badge>
                </div>

                {step.skills && step.skills.length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium mb-2">Skills to Learn:</h4>
                    <div className="flex flex-wrap gap-1">
                      {step.skills.map((skill, skillIndex) => (
                        <Badge key={skillIndex} variant="outline" className="text-xs">
                          {skill}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}

                {step.resources && step.resources.length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium mb-2 flex items-center gap-1">
                      <BookOpen className="h-4 w-4" />
                      Resources:
                    </h4>
                    <ul className="text-sm text-muted-foreground space-y-1">
                      {step.resources.map((resource, resourceIndex) => (
                        <li key={resourceIndex} className="flex items-start gap-2">
                          <span className="text-primary">•</span>
                          {resource}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      ))}
    </div>
  )
}
