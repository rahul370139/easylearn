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

const API_BASE_URL =
  normalizeApiBaseUrl(process.env.NEXT_PUBLIC_API_BASE_URL) ||
  (process.env.NODE_ENV === "development" ? "http://127.0.0.1:8000" : "")

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
    const url = `${API_BASE_URL}${endpoint}`
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
export const learnAPI = {
  // PDF Processing & Lesson Management
  distill: (file: File, ownerId: string) => {
    const formData = new FormData()
    formData.append("file", file)

    return fetch(`${API_BASE_URL}/api/distill?owner_id=${ownerId}`, {
      method: "POST",
      body: formData,
    }).then((res) => {
      if (!res.ok) throw new Error(`Distill failed: ${res.status}`)
      return res.json()
    })
  },

  getLessonContent: (lessonId: string, action: string) => apiCall<any>(`/api/lesson/${lessonId}/${action}`),

  generateLessonContent: (lessonId: string, action: string, data: any) =>
    apiCall<any>(`/api/lesson/${lessonId}/${action}`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  getLessonSummary: (data: any) =>
    apiCall<any>("/api/chat/lesson/summary", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  getLessonContentForChat: (lessonId: string, userId: string) =>
    apiCall<any>(`/api/chat/lesson/${lessonId}/content?user_id=${encodeURIComponent(userId)}`),

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

  // File upload for learn page
  uploadFile: async (file: File) => {
    try {
      const formData = new FormData()
      formData.append("file", file)

      return await apiCall("/api/learn/upload", {
        method: "POST",
        body: formData,
        headers: {}, // Let browser set Content-Type for FormData
      })
    } catch (error) {
      console.warn("File upload API failed")
      return { success: false, error: "Upload failed" }
    }
  },

  // Chat functionality for learn page
  chat: async (data: {
    message: string
    user_id: string
    file_id?: string
    experience_level?: string
    framework_focus?: string
  }) => {
    try {
      return await apiCall("/api/learn/chat", {
        method: "POST",
        body: JSON.stringify(data),
      })
    } catch (error) {
      console.warn("Chat API failed, using fallback response")
      return {
        response: "I'm currently experiencing technical difficulties. Please try again later.",
        type: "text",
      }
    }
  },
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

    const url = `${API_BASE_URL}/api/chat/upload?user_id=${encodeURIComponent(userId)}${explanationLevel ? `&explanation_level=${encodeURIComponent(explanationLevel)}` : ""}`

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

// Agentic AI Endpoints
export const agenticAPI = {
  // Intent Detection & Routing
  routeMessage: (data: { message: string; pdf_id?: string; user_id?: string }) =>
    apiCall<{
      intent: string
      confidence: number
      message: string
      context: any
      suggestions?: string[]
    }>("/api/agent/route", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  // Summary Agent
  generateSummary: (data: { pdf_id: string; user_id: string; topic?: string }) =>
    apiCall<{
      summary: string
      concept_map: any
      key_points: string[]
      page_references: any
    }>("/api/agent/summary", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  // Diagnostic Agent
  startDiagnostic: (data: { pdf_id: string; user_id: string; topic?: string; num?: number }) =>
    apiCall<{
      questions: Array<{
        id: string
        question: string
        options: string[]
        answer_idx: number
        topic: string
        generated_at: string
        fallback: boolean
      }>
      mastery_before: any
      diagnostic_plan: any
      session_id: string
      created_at: string
      adaptive: boolean
    }>("/api/agent/diagnostic", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  processDiagnosticResults: (data: {
    pdf_id: string
    user_id: string
    topic?: string
    user_answers: Array<{
      question_index: number
      selected_answer: string
      is_correct: boolean
    }>
    session_id: string
  }) =>
    apiCall<{
      status: string
      results: {
        mastery_after: any
        skill_gaps: string[]
        recommendations: string[]
        improvement_score: number
        next_steps: string[]
      }
    }>("/api/agent/diagnostic/results", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  // Mastery Tracking - with proper error handling for anonymous users
  getMastery: async (userId: string, topic?: string) => {
    // Don't make API call for anonymous users
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
      // Return default mastery data if API fails
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

  // Content Generation
  generateWorkflow: (data: { pdf_id: string; user_id: string; topic?: string }) =>
    apiCall<{
      workflow: Array<{
        step: number
        action: string
        description: string
        estimated_time?: string
        resources?: string[]
      }>
      total_steps: number
      estimated_duration: string
      difficulty_level: string
    }>("/api/agent/workflow", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  generateFlashcards: (data: { pdf_id: string; user_id: string; topic?: string; num?: number }) =>
    apiCall<{
      flashcards: Array<{
        front: string
        back: string
      }>
      total_cards: number
      difficulty_level: string
    }>("/api/agent/flashcards", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  generateQuiz: (data: { pdf_id: string; user_id: string; topic?: string; num?: number }) =>
    apiCall<{
      questions: Array<{
        question: string
        options: string[]
        correct_answer: string
        explanation?: string
      }>
      total_questions: number
      difficulty_level: string
    }>("/api/agent/quiz", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  generateContent: async (data: {
    pdf_id: string
    user_id: string
    content_type: "lesson" | "quiz" | "flashcards" | "workflow"
    topic?: string
    difficulty?: string
  }) => {
    // Route to appropriate content generation endpoint
    switch (data.content_type) {
      case "quiz":
        return agenticAPI.generateQuiz({
          pdf_id: data.pdf_id,
          user_id: data.user_id,
          topic: data.topic,
          num: 10,
        })
      case "flashcards":
        return agenticAPI.generateFlashcards({
          pdf_id: data.pdf_id,
          user_id: data.user_id,
          topic: data.topic,
          num: 15,
        })
      case "workflow":
        return agenticAPI.generateWorkflow({
          pdf_id: data.pdf_id,
          user_id: data.user_id,
          topic: data.topic,
        })
      case "lesson":
        // For lesson generation, we'll use the learn API
        return learnAPI.generateLessonContent(data.pdf_id, "lesson", {
          user_id: data.user_id,
          difficulty: data.difficulty,
          topic: data.topic,
        })
      default:
        throw new Error(`Unsupported content type: ${data.content_type}`)
    }
  },

  // System Testing
  testSystem: () => apiCall<{ status: string; message: string }>("/api/agent/test"),

  // Additional methods for agentic interface
  detectIntent: async (data: { message: string; user_id: string }) => {
    try {
      return await apiCall("/api/agent/intent", {
        method: "POST",
        body: JSON.stringify(data),
      })
    } catch (error) {
      return { intent: "general", confidence: 0.5 }
    }
  },

  runDiagnostic: async (data: { topic: string; user_id: string }) => {
    try {
      return await apiCall("/api/agent/diagnostic", {
        method: "POST",
        body: JSON.stringify(data),
      })
    } catch (error) {
      return {
        diagnostic: {
          strengths: ["Basic understanding"],
          weaknesses: ["Advanced concepts"],
          recommendations: ["Practice more examples"],
        },
      }
    }
  },
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
