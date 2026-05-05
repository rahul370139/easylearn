export interface LearningProgress {
  completed_lessons: number
  total_lessons: number
  progress_percentage: number
  hours_spent: number
  current_streak: number
  skills_learned: number
  career_advancement_percentage: number
  current_level: number
  next_milestone: string
}

export interface RecentActivityItem {
  type: string
  title: string
  date: string
  progress?: number
  status?: string
}

export interface Achievement {
  title: string
  description: string
  earned_date: string
  badge_type: string
  icon: string
}

export interface DashboardData {
  progress: LearningProgress
  recent_activity: RecentActivityItem[]
  achievements: Achievement[]
  saved_content: Array<{
    id: string
    title: string
    type: string
    date_saved: string
  }>
  chat_history: Array<{
    id: string
    summary: string
    date: string
    topic: string
  }>
  recommendations: {
    next_lessons: Array<{
      id: string
      title: string
      description: string
      estimated_time: string
      difficulty: string
      priority: number
    }>
    career_opportunities: Array<{
      title: string
      company: string
      match_score: number
      salary_range: string
      location: string
      skills_required: string[]
    }>
    skill_gaps: Array<{
      skill: string
      current_level: number
      target_level: number
      priority: string
      market_demand: string
    }>
    market_trends: Array<{
      trend: string
      description: string
      growth_rate: string
      relevance_score: number
    }>
    general_recommendations: Array<{
      id: string
      title: string
      description: string
      link: string
    }>
  }
  analytics: {
    learning_timeline: Array<{
      date: string
      lessons: number
      hours: number
      skills_gained: number
    }>
    skill_levels: Array<{
      skill: string
      level: number
      max_level: number
      progress_percentage: number
    }>
    time_distribution: Array<{
      activity: string
      hours: number
      percentage: number
      color: string
    }>
    career_progress: Array<{
      milestone: string
      completed: boolean
      date?: string
      progress_percentage: number
    }>
  }
  user_role: "student" | "professional"
}
