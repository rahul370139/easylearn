"use client"

import { useEffect, useState } from "react"
import { careerAPI } from "@/lib/api"
import { useAuth } from "@/components/auth-provider"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Separator } from "@/components/ui/separator"
import { toast } from "@/components/ui/use-toast"
import {
  Upload,
  FileText,
  Brain,
  Target,
  TrendingUp,
  Sparkles,
  AlertTriangle,
  CheckCircle2,
  Code,
  GraduationCap,
  Plus,
  X,
  Loader2,
  Briefcase,
  Calendar,
  BookOpen,
  Lightbulb,
} from "lucide-react"

interface ParsedResume {
  name?: string | null
  headline?: string | null
  years_of_experience?: number | null
  current_role?: string | null
  current_company?: string | null
  skills: string[]
  experience: Array<{
    role: string
    company: string
    start?: string | null
    end?: string | null
    achievements?: string[]
  }>
  education: Array<{ degree: string; school: string; year?: string | null }>
  projects: Array<{ name: string; description: string; stack?: string[] }>
  certifications?: string[]
  languages?: string[]
}

interface CareerPlanResponse {
  target_role: string
  interests: string[]
  onet_match?: {
    title?: string | null
    soc_code?: string | null
    salary_low?: number | null
    salary_high?: number | null
    growth_pct?: number | null
  }
  plan: {
    skill_gap?: {
      strengths?: string[]
      transferable?: string[]
      gaps?: string[]
      blockers?: string[]
      readiness_score?: number
    }
    roadmap?: Record<
      string,
      {
        title?: string
        duration?: string
        salary_range?: string
        skills_to_acquire?: string[]
        responsibilities?: string[]
        milestones?: string[]
      }
    >
    ninety_day_plan?: Array<{
      week: string
      focus: string
      actions: string[]
      deliverable: string
    }>
    projects_to_build?: Array<{
      title: string
      why: string
      stack?: string[]
      scope?: string
      stretch_goal?: string
    }>
    resources?: Array<{ title: string; type: string; why?: string }>
    interview_prep?: {
      core_topics?: string[]
      behavioral_themes?: string[]
      system_design_targets?: string[]
    }
    market_insights?: {
      salary_range?: string
      growth_outlook?: string
      hot_skills?: string[]
    }
  }
}

const POPULAR_ROLES = [
  "Data Scientist",
  "Software Engineer",
  "Machine Learning Engineer",
  "Product Manager",
  "DevOps Engineer",
  "Data Engineer",
  "Frontend Developer",
  "Backend Developer",
]

const INTEREST_SUGGESTIONS = [
  "Machine Learning",
  "Cloud / DevOps",
  "Product",
  "Data Engineering",
  "Generative AI",
  "Backend Systems",
  "Frontend / UX",
  "Computer Vision",
  "NLP",
  "Quant / Finance",
]

// localStorage key for persisting resume / role / interests across navigation.
// We deliberately don't persist the original File (browsers can't rehydrate
// File objects from JSON) or the generated plan (cheap to regenerate, plus
// it can get large).
const STORAGE_KEY = "trainpi:resume_upgrade_state:v1"

interface PersistedState {
  parsed: ParsedResume | null
  targetRole: string
  interests: string[]
  fileName: string | null
}

function loadPersisted(): PersistedState | null {
  if (typeof window === "undefined") return null
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw) as PersistedState
    if (!parsed || typeof parsed !== "object") return null
    return parsed
  } catch {
    return null
  }
}

function savePersisted(state: PersistedState) {
  if (typeof window === "undefined") return
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(state))
  } catch {
    // ignore quota errors
  }
}

export function ResumeCareerUpgrade() {
  const { user } = useAuth()
  const [resumeFile, setResumeFile] = useState<File | null>(null)
  const [persistedFileName, setPersistedFileName] = useState<string | null>(null)
  const [parsed, setParsed] = useState<ParsedResume | null>(null)
  const [parsing, setParsing] = useState(false)
  const [building, setBuilding] = useState(false)
  const [targetRole, setTargetRole] = useState("")
  const [interests, setInterests] = useState<string[]>([])
  const [customInterest, setCustomInterest] = useState("")
  const [plan, setPlan] = useState<CareerPlanResponse | null>(null)

  // Hydrate from localStorage on mount.
  useEffect(() => {
    const persisted = loadPersisted()
    if (!persisted) return
    if (persisted.parsed) setParsed(persisted.parsed)
    if (persisted.targetRole) setTargetRole(persisted.targetRole)
    if (persisted.interests) setInterests(persisted.interests)
    if (persisted.fileName) setPersistedFileName(persisted.fileName)
  }, [])

  // Save whenever the meaningful inputs change.
  useEffect(() => {
    if (!parsed && !targetRole && interests.length === 0) return
    savePersisted({
      parsed,
      targetRole,
      interests,
      fileName: resumeFile?.name ?? persistedFileName,
    })
  }, [parsed, targetRole, interests, resumeFile, persistedFileName])

  const clearSaved = () => {
    if (typeof window !== "undefined") window.localStorage.removeItem(STORAGE_KEY)
    setResumeFile(null)
    setPersistedFileName(null)
    setParsed(null)
    setTargetRole("")
    setInterests([])
    setPlan(null)
  }

  const handleFile = async (file: File) => {
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      toast({ title: "PDF only", description: "Please upload a PDF resume.", variant: "destructive" })
      return
    }
    setResumeFile(file)
    setParsing(true)
    setPlan(null)
    try {
      const res = await careerAPI.parseResume(file)
      setParsed(res.resume)
      toast({
        title: "Resume parsed",
        description: `Extracted ${res.resume.skills?.length || 0} skills, ${res.resume.experience?.length || 0} roles.`,
      })
    } catch (err) {
      console.error(err)
      toast({
        title: "Could not parse resume",
        description: "If the PDF is scanned (image-only), try a text-based PDF.",
        variant: "destructive",
      })
    } finally {
      setParsing(false)
    }
  }

  const toggleInterest = (interest: string) => {
    setInterests((prev) => (prev.includes(interest) ? prev.filter((i) => i !== interest) : [...prev, interest]))
  }

  const addCustomInterest = () => {
    const v = customInterest.trim()
    if (!v) return
    if (!interests.includes(v)) setInterests([...interests, v])
    setCustomInterest("")
  }

  const removeSkill = (skill: string) => {
    if (!parsed) return
    setParsed({ ...parsed, skills: parsed.skills.filter((s) => s !== skill) })
  }

  const handleBuildPlan = async () => {
    if (!parsed || !targetRole) return
    setBuilding(true)
    try {
      // Prefer the one-shot endpoint when we still have the source PDF in-memory.
      // It now persists server-side automatically when user_id is provided.
      const result = resumeFile
        ? await careerAPI.upgrade(resumeFile, targetRole, interests, user?.id)
        : await careerAPI.buildPlan({
            resume: parsed,
            target_role: targetRole,
            interests,
          })
      setPlan(result)
      // Fallback persistence path for "build from parsed profile" mode
      // (e.g. after reload when only cached parsed JSON exists, no File object).
      if (user?.id && !resumeFile) {
        try {
          await careerAPI.saveCareerPlanSnapshot(user.id, result as Record<string, unknown>)
        } catch (persistErr) {
          console.warn("Career plan not persisted to server:", persistErr)
        }
      }
    } catch (err) {
      console.error(err)
      toast({
        title: "Plan generation failed",
        description: "Please try again in a moment.",
        variant: "destructive",
      })
    } finally {
      setBuilding(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Step 1 — upload resume */}
      <Card className="border-2 border-dashed">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            1. Upload your resume
          </CardTitle>
          <CardDescription>
            We'll extract your skills, experience, and projects. Nothing is hardcoded — every field comes from your PDF.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap items-center gap-3">
            <input
              id="resume-upload"
              type="file"
              accept=".pdf"
              className="hidden"
              onChange={(e) => {
                const f = e.target.files?.[0]
                if (f) handleFile(f)
              }}
            />
            <Label htmlFor="resume-upload">
              <Button asChild variant="outline" disabled={parsing}>
                <span>
                  <Upload className="mr-2 h-4 w-4" />
                  {parsing ? "Parsing…" : resumeFile || parsed ? "Replace PDF" : "Choose PDF"}
                </span>
              </Button>
            </Label>
            {(resumeFile || persistedFileName) && (
              <span className="text-sm text-muted-foreground truncate max-w-md">
                {resumeFile?.name || persistedFileName}
                {!resumeFile && parsed && (
                  <Badge variant="outline" className="ml-2 text-[10px]">
                    cached
                  </Badge>
                )}
              </span>
            )}
            {parsing && <Loader2 className="h-4 w-4 animate-spin" />}
            {(parsed || resumeFile) && (
              <Button variant="ghost" size="sm" onClick={clearSaved} className="ml-auto">
                Clear
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Step 2 — review parsed resume */}
      {parsed && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Brain className="h-5 w-5" />
              2. Review what we found
            </CardTitle>
            <CardDescription>
              {parsed.name ? `${parsed.name}` : "Profile"}
              {parsed.headline ? ` · ${parsed.headline}` : ""}
              {parsed.years_of_experience ? ` · ~${parsed.years_of_experience} yrs` : ""}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label className="text-sm">Skills (click ✕ to remove anything wrong)</Label>
              <div className="mt-2 flex flex-wrap gap-2">
                {parsed.skills.length === 0 && (
                  <p className="text-sm text-muted-foreground">No skills extracted — try a more detailed resume.</p>
                )}
                {parsed.skills.map((s) => (
                  <Badge key={s} variant="secondary" className="flex items-center gap-1">
                    {s}
                    <X className="h-3 w-3 cursor-pointer hover:text-red-500" onClick={() => removeSkill(s)} />
                  </Badge>
                ))}
              </div>
            </div>

            {parsed.experience.length > 0 && (
              <div>
                <Label className="text-sm">Experience</Label>
                <div className="mt-2 space-y-2">
                  {parsed.experience.slice(0, 4).map((exp, i) => (
                    <div key={i} className="text-sm">
                      <span className="font-medium">{exp.role}</span>
                      <span className="text-muted-foreground"> · {exp.company}</span>
                      {(exp.start || exp.end) && (
                        <span className="text-muted-foreground">
                          {" "}
                          ({exp.start || "?"} – {exp.end || "present"})
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {parsed.education.length > 0 && (
              <div>
                <Label className="text-sm flex items-center gap-1">
                  <GraduationCap className="h-3 w-3" /> Education
                </Label>
                <div className="mt-2 space-y-1">
                  {parsed.education.map((ed, i) => (
                    <p key={i} className="text-sm text-muted-foreground">
                      {ed.degree} · {ed.school}
                      {ed.year ? ` · ${ed.year}` : ""}
                    </p>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Step 3 — target + interests + generate */}
      {parsed && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Target className="h-5 w-5" />
              3. Target role & interests
            </CardTitle>
            <CardDescription>
              We'll match this against the O*NET / BLS dataset and build a tailored plan.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="target-role">Target role</Label>
              <Input
                id="target-role"
                placeholder="e.g. Machine Learning Engineer"
                value={targetRole}
                onChange={(e) => setTargetRole(e.target.value)}
              />
              <div className="mt-2 flex flex-wrap gap-2">
                {POPULAR_ROLES.map((r) => (
                  <Button
                    key={r}
                    variant="outline"
                    size="sm"
                    className="h-7 text-xs"
                    onClick={() => setTargetRole(r)}
                  >
                    {r}
                  </Button>
                ))}
              </div>
            </div>

            <div>
              <Label>Interests (optional but useful)</Label>
              <div className="mt-2 flex flex-wrap gap-2">
                {INTEREST_SUGGESTIONS.map((i) => (
                  <Badge
                    key={i}
                    variant={interests.includes(i) ? "default" : "outline"}
                    className="cursor-pointer"
                    onClick={() => toggleInterest(i)}
                  >
                    {i}
                  </Badge>
                ))}
              </div>
              <div className="mt-2 flex gap-2">
                <Input
                  placeholder="Add custom interest…"
                  value={customInterest}
                  onChange={(e) => setCustomInterest(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), addCustomInterest())}
                />
                <Button variant="outline" size="icon" onClick={addCustomInterest}>
                  <Plus className="h-4 w-4" />
                </Button>
              </div>
              {interests.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-2">
                  {interests.map((i) => (
                    <Badge key={i} className="flex items-center gap-1">
                      {i}
                      <X className="h-3 w-3 cursor-pointer" onClick={() => toggleInterest(i)} />
                    </Badge>
                  ))}
                </div>
              )}
            </div>

            <Button
              onClick={handleBuildPlan}
              disabled={!targetRole || building}
              className="w-full bg-gradient-to-r from-blue-600 to-purple-600"
            >
              {building ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Sparkles className="mr-2 h-4 w-4" />}
              {building ? "Building plan…" : "Build my upgrade plan"}
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Plan output */}
      {plan && <PlanView plan={plan} userName={parsed?.name ?? null} />}
    </div>
  )
}

function PlanView({ plan, userName }: { plan: CareerPlanResponse; userName: string | null }) {
  const gap = plan.plan.skill_gap ?? {}
  const market = plan.plan.market_insights ?? {}
  const onet = plan.onet_match
  const readiness = typeof gap.readiness_score === "number" ? Math.max(0, Math.min(100, gap.readiness_score)) : null

  return (
    <div className="space-y-6">
      <Card className="border-blue-200 dark:border-blue-900">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-blue-600" />
            Your upgrade plan: {plan.target_role}
          </CardTitle>
          <CardDescription>
            {userName ? `${userName}, here's where you stand and what to do next.` : "Here's where you stand and what to do next."}
            {onet?.title ? ` Anchored to O*NET row "${onet.title}".` : ""}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Stat label="Readiness" value={readiness !== null ? `${readiness}%` : "—"} icon={<Target className="h-4 w-4" />} />
            <Stat
              label="Salary band"
              value={market.salary_range || (onet?.salary_low && onet?.salary_high ? `$${onet.salary_low.toLocaleString()} – $${onet.salary_high.toLocaleString()}` : "—")}
              icon={<Briefcase className="h-4 w-4" />}
            />
            <Stat
              label="Growth"
              value={market.growth_outlook || (onet?.growth_pct != null ? `${onet.growth_pct}%` : "—")}
              icon={<TrendingUp className="h-4 w-4" />}
            />
          </div>
          {readiness !== null && (
            <div className="mt-4">
              <Progress value={readiness} className="h-2" />
            </div>
          )}
        </CardContent>
      </Card>

      {/* Skill gap */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="h-5 w-5" />
            Skill gap analysis
          </CardTitle>
        </CardHeader>
        <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <GapList
            label="Strengths"
            items={gap.strengths || []}
            tone="green"
            icon={<CheckCircle2 className="h-4 w-4 text-green-600" />}
          />
          <GapList
            label="Transferable"
            items={gap.transferable || []}
            tone="blue"
            icon={<Sparkles className="h-4 w-4 text-blue-600" />}
          />
          <GapList
            label="Gaps to close"
            items={gap.gaps || []}
            tone="orange"
            icon={<AlertTriangle className="h-4 w-4 text-orange-600" />}
          />
          <GapList
            label="Hard blockers"
            items={gap.blockers || []}
            tone="red"
            icon={<AlertTriangle className="h-4 w-4 text-red-600" />}
          />
        </CardContent>
      </Card>

      {/* Roadmap */}
      {plan.plan.roadmap && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              3-stage roadmap
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {Object.entries(plan.plan.roadmap).map(([level, details]) => (
                <Card key={level} className="border-2">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-base">{details.title || level}</CardTitle>
                    <CardDescription className="text-xs">
                      {details.duration} · {details.salary_range}
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {details.skills_to_acquire && details.skills_to_acquire.length > 0 && (
                      <div>
                        <p className="text-xs font-medium mb-1">Skills to acquire</p>
                        <div className="flex flex-wrap gap-1">
                          {details.skills_to_acquire.map((s, i) => (
                            <Badge key={i} variant="outline" className="text-xs">
                              {s}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}
                    {details.responsibilities && details.responsibilities.length > 0 && (
                      <div>
                        <p className="text-xs font-medium mb-1">Responsibilities</p>
                        <ul className="text-xs space-y-1 text-muted-foreground">
                          {details.responsibilities.slice(0, 3).map((r, i) => (
                            <li key={i}>• {r}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {details.milestones && details.milestones.length > 0 && (
                      <div>
                        <p className="text-xs font-medium mb-1">Milestones</p>
                        <ul className="text-xs space-y-1 text-muted-foreground">
                          {details.milestones.slice(0, 3).map((m, i) => (
                            <li key={i}>→ {m}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* 90-day plan */}
      {plan.plan.ninety_day_plan && plan.plan.ninety_day_plan.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calendar className="h-5 w-5" />
              First 90 days
            </CardTitle>
            <CardDescription>Concrete weekly cadence — stick this on your calendar.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {plan.plan.ninety_day_plan.map((w, i) => (
                <div key={i} className="border-l-2 border-blue-500 pl-4">
                  <p className="text-sm font-semibold">
                    Week {w.week} — {w.focus}
                  </p>
                  <ul className="mt-1 text-sm text-muted-foreground space-y-1">
                    {w.actions?.map((a, ai) => (
                      <li key={ai}>• {a}</li>
                    ))}
                  </ul>
                  {w.deliverable && (
                    <p className="mt-1 text-xs">
                      <span className="font-medium">Deliverable:</span> {w.deliverable}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Projects */}
      {plan.plan.projects_to_build && plan.plan.projects_to_build.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Code className="h-5 w-5" />
              Projects to build
            </CardTitle>
            <CardDescription>Portfolio-grade work tailored to your existing stack.</CardDescription>
          </CardHeader>
          <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {plan.plan.projects_to_build.map((p, i) => (
              <Card key={i}>
                <CardHeader className="pb-2">
                  <CardTitle className="text-base">{p.title}</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2 text-sm">
                  <p className="text-muted-foreground">{p.why}</p>
                  {p.scope && <p><span className="font-medium">Scope:</span> {p.scope}</p>}
                  {p.stretch_goal && (
                    <p><span className="font-medium">Stretch:</span> {p.stretch_goal}</p>
                  )}
                  {p.stack && p.stack.length > 0 && (
                    <div className="flex flex-wrap gap-1 pt-1">
                      {p.stack.map((s, si) => (
                        <Badge key={si} variant="outline" className="text-xs">
                          {s}
                        </Badge>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Resources + interview prep */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {plan.plan.resources && plan.plan.resources.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <BookOpen className="h-4 w-4" />
                Resources
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2 text-sm">
                {plan.plan.resources.map((r, i) => (
                  <li key={i}>
                    <span className="font-medium">{r.title}</span>{" "}
                    <Badge variant="outline" className="text-[10px] ml-1">
                      {r.type}
                    </Badge>
                    {r.why && <p className="text-muted-foreground text-xs mt-0.5">{r.why}</p>}
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        )}

        {plan.plan.interview_prep && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <Lightbulb className="h-4 w-4" />
                Interview prep
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              {plan.plan.interview_prep.core_topics && plan.plan.interview_prep.core_topics.length > 0 && (
                <div>
                  <p className="font-medium text-xs mb-1">Core topics</p>
                  <div className="flex flex-wrap gap-1">
                    {plan.plan.interview_prep.core_topics.map((t, i) => (
                      <Badge key={i} variant="outline" className="text-xs">
                        {t}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
              {plan.plan.interview_prep.behavioral_themes && plan.plan.interview_prep.behavioral_themes.length > 0 && (
                <div>
                  <p className="font-medium text-xs mb-1">Behavioral STAR themes (from your resume)</p>
                  <ul className="text-xs space-y-1 text-muted-foreground">
                    {plan.plan.interview_prep.behavioral_themes.map((t, i) => (
                      <li key={i}>• {t}</li>
                    ))}
                  </ul>
                </div>
              )}
              {plan.plan.interview_prep.system_design_targets && plan.plan.interview_prep.system_design_targets.length > 0 && (
                <div>
                  <p className="font-medium text-xs mb-1">System design targets</p>
                  <ul className="text-xs space-y-1 text-muted-foreground">
                    {plan.plan.interview_prep.system_design_targets.map((t, i) => (
                      <li key={i}>→ {t}</li>
                    ))}
                  </ul>
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </div>

      {market.hot_skills && market.hot_skills.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Hot skills in this market</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {market.hot_skills.map((s, i) => (
                <Badge key={i} variant="default">
                  {s}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

function Stat({ label, value, icon }: { label: string; value: string; icon: React.ReactNode }) {
  return (
    <div className="rounded-lg border p-3">
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        {icon}
        {label}
      </div>
      <p className="mt-1 text-lg font-semibold">{value}</p>
    </div>
  )
}

function GapList({
  label,
  items,
  tone,
  icon,
}: {
  label: string
  items: string[]
  tone: "green" | "blue" | "orange" | "red"
  icon: React.ReactNode
}) {
  const toneClass: Record<typeof tone, string> = {
    green: "border-green-200 bg-green-50 dark:bg-green-950/20",
    blue: "border-blue-200 bg-blue-50 dark:bg-blue-950/20",
    orange: "border-orange-200 bg-orange-50 dark:bg-orange-950/20",
    red: "border-red-200 bg-red-50 dark:bg-red-950/20",
  }
  return (
    <div className={`rounded-lg border p-3 ${toneClass[tone]}`}>
      <div className="flex items-center gap-2 text-sm font-medium">
        {icon}
        {label}
        <span className="text-xs text-muted-foreground">({items.length})</span>
      </div>
      {items.length === 0 ? (
        <p className="mt-2 text-xs text-muted-foreground">— none —</p>
      ) : (
        <ul className="mt-2 space-y-1 text-sm">
          {items.map((it, i) => (
            <li key={i}>• {it}</li>
          ))}
        </ul>
      )}
    </div>
  )
}
