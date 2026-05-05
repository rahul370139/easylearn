# SkillSpring - AI-Powered Microlearning Platform

A modern, intelligent microlearning platform built with Next.js 14, TypeScript, and AI integration to provide personalized learning experiences.

Demo Preview: https://skillspring001.vercel.app/

Backend Repo: https://github.com/rahul370139/Backend_skillspring


## 🚀 Features

### Core Learning Features
- **AI-Powered Learning**: Intelligent content analysis and personalized learning paths
- **PDF Document Processing**: Upload and analyze PDF documents for learning content
- **Interactive Lessons**: Dynamic lesson generation with customizable difficulty levels
- **Smart Summaries**: AI-generated summaries with key points extraction
- **Flashcards**: Automated flashcard creation for better retention
- **Interactive Quizzes**: AI-generated quizzes with multiple choice questions
- **Workflow Diagrams**: Visual workflow generation using Mermaid diagrams
- **Progress Tracking**: Comprehensive learning progress monitoring

### User Experience Features
- **Responsive Design**: Mobile-first design that works on all devices
- **Dark/Light Mode**: Theme switching with system preference detection
- **Real-time Chat**: AI-powered chat interface for learning assistance
- **File Upload**: Drag-and-drop PDF upload with progress indicators
- **Quick Actions**: One-click access to summaries, lessons, quizzes, and flashcards
- **Learning Settings**: Customizable experience level and framework preferences

### Authentication & User Management
- **Supabase Integration**: Secure authentication and user management
- **Social Login**: Multiple authentication providers
- **User Profiles**: Personalized user experience and progress tracking
- **Session Management**: Secure session handling and persistence

## 📱 Pages & Routes

### Public Pages
- **Homepage** (`/`): Landing page with platform overview and features
- **Login** (`/login`): User authentication and login interface
- **Auth Callback** (`/auth/callback`): OAuth callback handling

### Protected Pages
- **Dashboard** (`/dashboard`): User dashboard with learning analytics and progress
- **Learn** (`/learn`): Main learning interface with AI chat and content processing
- **Career Discovery** (`/career`): Career path exploration and guidance
- **Career Discover** (`/career/discover`): Detailed career insights and recommendations

## 🛠️ Technical Stack

### Frontend
- **Next.js 14**: React framework with App Router
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Utility-first CSS framework
- **shadcn/ui**: Modern UI component library
- **Lucide React**: Beautiful icon library

### AI & Backend Integration
- **OpenAI Integration**: AI-powered content generation and analysis
- **Supabase**: Backend-as-a-Service for authentication and data
- **React Markdown**: Markdown rendering for content display
- **Remark GFM**: GitHub Flavored Markdown support

### State Management & Hooks
- **React Hooks**: Modern React state management
- **Custom Hooks**: Reusable logic for authentication, mobile detection, and toasts
- **Context API**: Global state management for authentication and theme

## 🎨 UI Components

### Core Components
- **Navigation**: Responsive navbar with mobile menu
- **Cards**: Learning content cards with rich media support
- **Forms**: Interactive forms with validation
- **Charts**: Progress visualization and analytics
- **Modals**: Overlay components for user interactions

### Specialized Components
- **Lesson Display**: Interactive lesson viewer with progress tracking
- **Flashcard Player**: Animated flashcard interface
- **Quiz Player**: Interactive quiz interface with scoring
- **Chat Interface**: AI-powered chat with file upload support
- **Progress Overview**: Visual learning progress indicators
- **Achievements**: Gamification elements for user engagement

## 🔧 Configuration

### Environment Setup
- **Vercel Deployment**: Optimized for Vercel hosting
- **Environment Variables**: Secure configuration management
- **Build Optimization**: Production-ready build configuration

### Development Tools
- **ESLint**: Code quality and consistency
- **TypeScript**: Static type checking
- **PostCSS**: CSS processing and optimization
- **Tailwind**: Utility-first CSS framework

## 🚀 Getting Started

### Prerequisites
- Node.js 18+ 
- pnpm package manager
- Supabase account for backend services
- OpenAI API key for AI features

### Installation
```bash
# Clone the repository
git clone https://github.com/yourusername/skillspring.git

# Install dependencies
pnpm install

# Set up environment variables
# Create `frontend/.env.local` (Next.js reads this automatically in dev)

# Run development server
pnpm dev

# Build for production
pnpm build
```

### Environment Variables
```env
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
OPENAI_API_KEY=your_openai_api_key

# Public backend base URL (no trailing slash)
# Local dev example:
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
# Production example (must be reachable from browsers, NOT localhost):
# NEXT_PUBLIC_API_BASE_URL=https://api.yourdomain.com
```

## 📊 Learning Analytics

- **Progress Tracking**: Visual progress indicators and completion rates
- **Learning Analytics**: Detailed insights into learning patterns
- **Achievement System**: Gamified learning milestones
- **Performance Metrics**: Quiz scores and learning efficiency

## 🔒 Security Features

- **Authentication**: Secure user authentication with Supabase
- **File Validation**: Secure PDF upload with validation
- **API Protection**: Protected API endpoints with user verification
- **Data Privacy**: User data protection and privacy compliance

## 🌟 Future Enhancements

- **Mobile App**: Native mobile applications
- **Offline Support**: Offline learning capabilities
- **Advanced Analytics**: Machine learning insights
- **Collaborative Learning**: Group learning features
- **Content Marketplace**: Third-party content integration

Try out my demo here: https://skillspring001.vercel.app/
