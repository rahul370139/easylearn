function normalizeApiBaseUrl(raw: string | undefined): string {
  const trimmed = (raw ?? "").trim().replace(/\/+$/, "")
  if (!trimmed) return ""

  // `0.0.0.0` is a bind address, not a browser-routable host.
  if (trimmed.includes("0.0.0.0")) {
    throw new Error(
      "Invalid NEXT_PUBLIC_API_BASE_URL: do not use 0.0.0.0. Use http://127.0.0.1:8000 locally or your public VPS URL in production.",
    )
  }

  return trimmed
}

function getApiBaseUrl(): string {
  const fromEnv = normalizeApiBaseUrl(process.env.NEXT_PUBLIC_API_BASE_URL)

  // In production on Vercel the site is served over HTTPS.
  // If the backend is only available over plain HTTP (e.g. VPS IP:8000),
  // direct browser calls will be blocked as mixed content.
  // In that case we rely on Next.js rewrites and call same-origin paths.
  if (typeof window !== "undefined") {
    if (window.location.protocol === "https:" && fromEnv.startsWith("http://")) {
      return ""
    }
  }

  if (fromEnv) return fromEnv
  if (process.env.NODE_ENV === "development") return "http://127.0.0.1:8000"
  return ""
}

const API_BASE_URL = getApiBaseUrl()

function urlFor(pathWithLeadingSlash: string): string {
  return API_BASE_URL ? `${API_BASE_URL}${pathWithLeadingSlash}` : pathWithLeadingSlash
}

interface ApiResponse<T = any> {
  data?: T
  error?: string
  message?: string
}

async function apiCall<T = any>(endpoint: string, options: RequestInit = {}): Promise<T> {
  try {
    // If API_BASE_URL is empty, we call same-origin endpoints.
    // This is useful on Vercel with Next.js rewrites proxying `/api/*` and `/health` to the backend,
    // and avoids browser mixed-content/CORS issues when the backend is only available over plain HTTP.
    const url = urlFor(endpoint)
    const response = await fetch(url, {
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
      ...options,
    })

    if (!response.ok) {
      const errorData = await response.text()
      throw new Error(`API Error ${response.status}: ${errorData}`)
    }

    const data = await response.json()
    return data
  } catch (error) {
    console.error(`API call failed for ${endpoint}:`, error)
    throw error
  }
}

// Health & Debug Endpoints
export const healthAPI = {
  check: () => apiCall<{ status: string }>("/health"),
  test: () => apiCall<{ message: string }>("/api/test"),
  debugLesson: (lessonId: string) => apiCall<any>(`/api/debug/lesson/${lessonId}`),
}

// Learn Page Endpoints
//
// Quick action content generation (summary / lesson / quiz / flashcards /
// workflow / diagnostic) deliberately does NOT live here. Those flow through
// `chatAPI.sendMessage`, which the backend routes by intent in
// `process_chat_message`. Keeping a single path avoids two diverging
// generators and the hardcoded "API Development" placeholders we used to
// have on the per-lesson endpoints.
export const learnAPI = {
  // PDF Processing & Lesson Management
  distill: (file: File, ownerId: string) => {
    const formData = new FormData()
    formData.append("file", file)

    const url = urlFor(`/api/distill?owner_id=${encodeURIComponent(ownerId)}`)
    return fetch(url, {
      method: "POST",
      body: formData,
    }).then((res) => {
      if (!res.ok) throw new Error(`Distill failed: ${res.status}`)
      return res.json()
    })
  },

  // Framework & Skills
  getFrameworks: () => apiCall<string[]>("/api/frameworks"),
  getSkills: () => apiCall<string[]>("/api/skills"),
  getExplanationLevels: () => apiCall<string[]>("/api/explanation-levels"),
  getLessonsByFramework: (framework: string) => apiCall<any[]>(`/api/lessons/framework/${framework}`),

  // Micro Lessons
  getMicroLessons: () => apiCall<any[]>("/api/lessons/micro"),
  searchLessons: (query: any) =>
    apiCall<any>("/api/lessons/search", {
      method: "POST",
      body: JSON.stringify(query),
    }),

  // User Progress
  completeLesson: (lessonId: string, userId: string, progressPercentage = 100.0) =>
    apiCall<any>(`/api/lessons/${lessonId}/complete`, {
      method: "POST",
      body: JSON.stringify({
        user_id: userId,
        progress_percentage: progressPercentage,
      }),
    }),

  getCompletedLessons: (userId: string) => apiCall<any[]>(`/api/users/${userId}/completed-lessons`),

  getUserProgress: (userId: string) => apiCall<any>(`/api/users/${userId}/progress`),
}

// Career Page Endpoints
export const careerAPI = {
  // Career Quiz & Matching
  getCareerQuiz: () => apiCall<any>("/api/career/quiz"),

  matchCareer: async (data: {
    user_id: string
    answers: Array<{ question_id: number; rating: number }>
  }) => {
    try {
      // Convert to the format expected by the backend
      const requestData = {
        owner_id: data.user_id,
        answers: data.answers.map(answer => answer.rating)
      }
      
      return await apiCall("/api/career/match", {
        method: "POST",
        body: JSON.stringify(requestData),
      })
    } catch (error) {
      console.warn("Career match API failed, using fallback")
      return {
        career_matches: [
          {
            career: "Software Engineer",
            match_score: 85,
            description: "Build and maintain software applications using various programming languages",
          },
          {
            career: "Data Scientist",
            match_score: 78,
            description: "Analyze complex data to help organizations make data-driven decisions",
          },
          {
            career: "UX Designer",
            match_score: 72,
            description: "Create intuitive and user-friendly digital experiences",
          },
        ],
      }
    }
  },

  // Career Roadmaps - Updated endpoints
  getCareerRoadmap: (careerTitle: string) => apiCall<any>(`/api/career/roadmap/${encodeURIComponent(careerTitle)}`),

  getAllRoadmaps: () => apiCall<any[]>("/api/career/roadmaps"),

  generateRoadmap: async (data: {
    target_role: string
    interests: string[]
    skills: string[]
    user_id: string
  }) => {
    try {
      return await apiCall("/api/career/roadmap/unified", {
        method: "POST",
        body: JSON.stringify(data),
      })
    } catch (error) {
      console.warn("Roadmap API failed, using fallback")
      return {
        career_title: data.target_role,
        total_duration: "6-12 months",
        difficulty_level: "intermediate",
        steps: [
          {
            step: 1,
            title: "Foundation Skills",
            description: `Learn the fundamental skills required for ${data.target_role}`,
            duration: "2-3 months",
            skills: data.skills.slice(0, 3),
            resources: ["Online courses", "Practice projects"],
          },
          {
            step: 2,
            title: "Intermediate Development",
            description: "Build practical projects and gain hands-on experience",
            duration: "3-4 months",
            skills: data.skills.slice(3, 6),
            resources: ["Portfolio projects", "Open source contributions"],
          },
          {
            step: 3,
            title: "Advanced Specialization",
            description: "Specialize in advanced topics and prepare for job market",
            duration: "2-3 months",
            skills: ["Advanced concepts", "Industry best practices"],
            resources: ["Certification programs", "Networking events"],
          },
        ],
      }
    }
  },

  // Career Planning
  generateCareerPlanning: (data: any) =>
    apiCall<any>("/api/career/planning", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  getCareerPlanningOptions: () => apiCall<any>("/api/career/planning/options"),

  generateComprehensivePlan: (data: any) =>
    apiCall<any>("/api/career/comprehensive-plan", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  getAvailableCareers: () => apiCall<string[]>("/api/career/available"),

  // Career Guidance & Advice
  getCareerGuidance: (data: any) =>
    apiCall<any>("/api/career/guidance", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  getCareerAdvice: (data: any) =>
    apiCall<any>("/api/career/advice", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  getCareerAdviceTopics: () => apiCall<string[]>("/api/career/advice/topics"),

  // Interview Preparation
  startInterviewSimulation: (data: any) =>
    apiCall<any>("/api/career/interview/start", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  submitInterviewAnswer: (data: any) =>
    apiCall<any>("/api/career/interview/answer", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  getInterviewRoles: () => apiCall<string[]>("/api/career/interview/roles"),

  generateInterviewPrep: (data: any) =>
    apiCall<any>("/api/career/roadmap/interview-prep", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  // Career Sessions
  getUserCareerSessions: (userId: string) => apiCall<any[]>(`/api/career/sessions/${userId}`),

  // Resume-driven career upgrade.
  // Step 1 — parse PDF: returns structured profile (skills, experience, projects).
  parseResume: (file: File) => {
    const formData = new FormData()
    formData.append("file", file)
    const url = urlFor("/api/career/resume/parse")
    return fetch(url, { method: "POST", body: formData }).then((res) => {
      if (!res.ok) throw new Error(`Resume parse failed: ${res.status}`)
      return res.json() as Promise<{ resume: any }>
    })
  },

  // Step 2 — given parsed resume + target role + interests, build the plan.
  buildPlan: (data: { resume: any; target_role: string; interests: string[] }) =>
    apiCall<any>("/api/career/plan/build", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  // One-shot: upload resume and get full upgrade payload (parsed + plan).
  upgrade: (file: File, target_role: string, interests: string[]) => {
    const formData = new FormData()
    formData.append("file", file)
    const qs = new URLSearchParams({ target_role, interests: interests.join(",") })
    const url = urlFor(`/api/career/upgrade?${qs.toString()}`)
    return fetch(url, { method: "POST", body: formData }).then((res) => {
      if (!res.ok) throw new Error(`Career upgrade failed: ${res.status}`)
      return res.json()
    })
  },
}

// Chat Page Endpoints
export const chatAPI = {
  // Chat Functionality
  sendMessage: (data: any) =>
    apiCall<any>("/api/chat", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  uploadFile: (file: File, userId: string, conversationId?: string, explanationLevel?: string) => {
    const formData = new FormData()
    formData.append("file", file)
    if (conversationId) formData.append("conversation_id", conversationId)

    const url = urlFor(
      `/api/chat/upload?user_id=${encodeURIComponent(userId)}${explanationLevel ? `&explanation_level=${encodeURIComponent(explanationLevel)}` : ""}`,
    )

    return fetch(url, {
      method: "POST",
      body: formData,
    }).then((res) => {
      if (!res.ok) throw new Error(`Upload failed: ${res.status}`)
      return res.json()
    })
  },

  ingestDistilled: (lessonId: string, userId: string, data: any) =>
    apiCall<any>(`/api/chat/ingest-distilled?lesson_id=${lessonId}&user_id=${encodeURIComponent(userId)}`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  // Chat Management
  getUserConversations: (userId: string) => apiCall<any[]>(`/api/chat/conversations/${userId}`),

  getConversation: (conversationId: string) => apiCall<any>(`/api/chat/conversation/${conversationId}`),

  getChatSideMenu: (userId: string) => apiCall<any>(`/api/chat/side-menu/${userId}`),

  // Chat Preferences
  updateExplanationLevel: (userId: string, level: string) =>
    apiCall<any>(`/api/chat/preferences/explanation-level`, {
      method: "PUT",
      body: JSON.stringify({ user_id: userId, level }),
    }),

  updateFrameworkPreference: (userId: string, framework: string) =>
    apiCall<any>(`/api/chat/preferences/framework`, {
      method: "PUT",
      body: JSON.stringify({ user_id: userId, framework }),
    }),
}

// Mastery & Diagnostic Result Endpoints
// Note: previously this object exposed many `/api/agent/*` and `/api/generate/*`
// wrappers. Those endpoints were placeholder/unreachable and have been removed
// from the backend. All "quick action" content generation (summary, lesson,
// quiz, flashcards, workflow, diagnostic) now flows through `chatAPI.sendMessage`
// which the backend routes by intent in `process_chat_message`.
export const agenticAPI = {
  // Mastery retrieval used by progress dashboards and the Learn header.
  getMastery: async (userId: string, topic?: string) => {
    if (!userId || userId === "anonymous-user" || userId === "anonymous") {
      return {
        status: "success",
        mastery: {
          overall_score: 0,
          topic_scores: {},
          skill_breakdown: {},
          learning_progress: {},
          recommended_topics: ["Upload a document to start tracking your progress"],
        },
      }
    }

    const url = `/api/agent/mastery/${userId}${topic ? `?topic=${encodeURIComponent(topic)}` : ""}`
    try {
      return await apiCall<{
        status: string
        mastery: {
          overall_score: number
          topic_scores: Record<string, number>
          skill_breakdown: Record<string, number>
          learning_progress: any
          recommended_topics: string[]
        }
      }>(url)
    } catch (error) {
      console.warn("Failed to fetch mastery data, returning defaults:", error)
      return {
        status: "success",
        mastery: {
          overall_score: 0,
          topic_scores: {},
          skill_breakdown: {},
          learning_progress: {},
          recommended_topics: ["Complete assessments to track your progress"],
        },
      }
    }
  },

  // Submit diagnostic answers; backend updates mastery and returns a topic breakdown.
  processDiagnosticResults: (data: {
    pdf_id?: string
    user_id: string
    topic?: string
    user_answers: Array<{
      question_index: number
      selected_answer: string
      is_correct: boolean
    }>
    session_id?: string
    questions?: Array<{ topic?: string }>
  }) =>
    apiCall<{
      status: string
      results: {
        results: {
          overall_score: number
          weak_areas: string[]
          strong_areas: string[]
          improvement_potential: number
        }
        remediation: { recommendations: string[] }
        mastery_update: { topic_scores: Record<string, number> }
        next_steps: string[]
      }
    }>("/api/agent/diagnostic/results", {
      method: "POST",
      body: JSON.stringify(data),
    }),
}

// Dashboard Page Endpoints
export const dashboardAPI = {
  // Dashboard Analytics
  getUserAnalytics: (userId: string) => apiCall<any>(`/api/dashboard/analytics/${userId}`),

  getUserProgress: (userId: string) => apiCall<any>(`/api/dashboard/progress/${userId}`),

  getUserAchievements: (userId: string) => apiCall<any>(`/api/dashboard/achievements/${userId}`),

  // Dashboard Recommendations
  getDashboardRecommendations: (data: any) =>
    apiCall<any>("/api/dashboard/recommendations", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  getCareerCoaching: (data: any) =>
    apiCall<any>("/api/dashboard/coaching", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  getStats: async (userId: string) => {
    try {
      return await apiCall(`/api/dashboard/stats/${userId}`)
    } catch (error) {
      return {
        stats: {
          lessonsCompleted: 0,
          hoursLearned: 0,
          skillsAcquired: 0,
          certificatesEarned: 0,
        },
      }
    }
  },

  getProgress: async (userId: string) => {
    try {
      return await apiCall(`/api/dashboard/progress/${userId}`)
    } catch (error) {
      return {
        progress: {
          currentStreak: 0,
          weeklyGoal: 10,
          weeklyProgress: 0,
          monthlyStats: [],
        },
      }
    }
  },

  getRecentActivity: async (userId: string) => {
    try {
      return await apiCall(`/api/dashboard/activity/${userId}`)
    } catch (error) {
      return {
        activities: [],
      }
    }
  },
}

// User Management Endpoints
export const userAPI = {
  updateUserRole: (userId: string, role: string) =>
    apiCall<any>(`/api/users/${userId}/role`, {
      method: "PUT",
      body: JSON.stringify({ role }),
    }),

  getUserRole: (userId: string) => apiCall<any>(`/api/users/${userId}/role`),
}

// Recommendation Endpoints
export const recommendationAPI = {
  getGeneralRecommendations: (data: any) =>
    apiCall<any>("/api/recommendations", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  getPersonalizedRecommendations: (data: any) =>
    apiCall<any>("/api/recommendations/personalized", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  getUserRecommendations: (userId: string) => apiCall<any>(`/api/recommendations/user/${userId}`),

  getMarketTrends: () => apiCall<any>("/api/recommendations/market-trends"),
  getLearningPaths: () => apiCall<any>("/api/recommendations/learning-paths"),
}

// Analytics Endpoints
export const analyticsAPI = {
  getUserAnalytics: (userId: string) => apiCall<any>(`/api/analytics/user/${userId}`),
}

export default {
  health: healthAPI,
  learn: learnAPI,
  career: careerAPI,
  chat: chatAPI,
  agentic: agenticAPI,
  dashboard: dashboardAPI,
  user: userAPI,
  recommendation: recommendationAPI,
  analytics: analyticsAPI,
}
