import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ArrowRight, BookOpen, TrendingUp, Zap, Star, CheckCircle } from "lucide-react"
import Image from "next/image"

export default function Landing() {
  return (
    <div className="space-y-20">
      {/* Hero Section */}
      <section className="text-center space-y-8 py-20">
        <div className="space-y-6">
          {/* TrainPI Logo and Name */}
          <div className="flex items-center justify-center space-x-4 mb-6">
            <Image
              src="https://hebbkx1anhila5yf.public.blob.vercel-storage.com/Capture.JPG-bBXs5Wjv3D3iFNOdJNFeQUnaJmtJkh.jpeg"
              alt="TrainPI Logo"
              width={60}
              height={60}
              className="rounded-lg"
            />
            <div className="text-center">
              <h1 className="text-5xl font-bold">
                <span className="text-blue-600">TRAIN</span>
                <span className="text-orange-500">PI</span>
              </h1>
              <Badge variant="secondary" className="px-4 py-1 text-sm font-medium mt-2">
                🚀 AI-Powered Learning Platform
              </Badge>
            </div>
          </div>

          <h2 className="text-3xl md:text-4xl font-bold text-slate-900 dark:text-white leading-tight">
            Master Your Future with
            <br />
            Smart Learning
          </h2>
          <p className="text-base text-slate-600 dark:text-slate-300 max-w-3xl mx-auto leading-relaxed">
            Transform your career with AI-powered micro-lessons, personalized career paths, and intelligent progress
            tracking. Learn faster, grow smarter, achieve more.
          </p>
        </div>

        <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
          <Link href="/learn">
            <Button
              size="lg"
              className="px-8 py-6 text-lg font-semibold bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 shadow-lg hover:shadow-xl transition-all duration-300"
            >
              Start Learning Now
              <ArrowRight className="ml-2 h-5 w-5" />
            </Button>
          </Link>
          <Link href="/career">
            <Button
              variant="outline"
              size="lg"
              className="px-8 py-6 text-lg font-semibold border-2 hover:bg-slate-50 dark:hover:bg-slate-800 transition-all duration-300 bg-transparent"
            >
              Explore Careers
            </Button>
          </Link>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-4xl mx-auto pt-16">
          <div className="text-center">
            <div className="text-3xl font-bold text-blue-600">10K+</div>
            <div className="text-slate-600 dark:text-slate-300">Active Learners</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-purple-600">500+</div>
            <div className="text-slate-600 dark:text-slate-300">Career Paths</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-indigo-600">95%</div>
            <div className="text-slate-600 dark:text-slate-300">Success Rate</div>
          </div>
        </div>
      </section>

      {/* Features Section - Now with Clickable Cards */}
      <section className="space-y-12">
        <div className="text-center space-y-4">
          <h2 className="text-3xl md:text-4xl font-bold text-slate-900 dark:text-white">Why Choose TrainPI?</h2>
          <p className="text-lg text-slate-600 dark:text-slate-300 max-w-2xl mx-auto">
            Experience the future of learning with our cutting-edge AI technology
          </p>
        </div>

        <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
          {/* Clickable Micro-Learning Card */}
          <Link href="/learn" className="block">
            <Card className="group hover:shadow-xl transition-all duration-300 border-0 bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-950/50 dark:to-indigo-950/50 cursor-pointer hover:-translate-y-2">
              <CardHeader>
                <div className="rounded-full bg-blue-100 dark:bg-blue-900 p-3 w-fit group-hover:scale-110 transition-transform">
                  <BookOpen className="h-6 w-6 text-blue-600 dark:text-blue-400" />
                </div>
                <CardTitle className="text-xl group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                  AI-Powered Micro-Learning
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-slate-600 dark:text-slate-300 mb-4">
                  Transform any document into bite-sized, interactive lessons with flashcards and quizzes powered by
                  advanced AI.
                </p>
                <div className="flex items-center text-blue-600 dark:text-blue-400 font-medium group-hover:translate-x-2 transition-transform">
                  Start Learning <ArrowRight className="ml-2 h-4 w-4" />
                </div>
              </CardContent>
            </Card>
          </Link>

          {/* Clickable Career Navigation Card */}
          <Link href="/career" className="block">
            <Card className="group hover:shadow-xl transition-all duration-300 border-0 bg-gradient-to-br from-purple-50 to-pink-50 dark:from-purple-950/50 dark:to-pink-950/50 cursor-pointer hover:-translate-y-2">
              <CardHeader>
                <div className="rounded-full bg-purple-100 dark:bg-purple-900 p-3 w-fit group-hover:scale-110 transition-transform">
                  <TrendingUp className="h-6 w-6 text-purple-600 dark:text-purple-400" />
                </div>
                <CardTitle className="text-xl group-hover:text-purple-600 dark:group-hover:text-purple-400 transition-colors">
                  Smart Career Navigation
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-slate-600 dark:text-slate-300 mb-4">
                  Discover your ideal career path with our intelligent assessment and get personalized roadmaps to
                  success.
                </p>
                <div className="flex items-center text-purple-600 dark:text-purple-400 font-medium group-hover:translate-x-2 transition-transform">
                  Explore Careers <ArrowRight className="ml-2 h-4 w-4" />
                </div>
              </CardContent>
            </Card>
          </Link>

          {/* Clickable Progress Tracking Card */}
          <Link href="/dashboard" className="block">
            <Card className="group hover:shadow-xl transition-all duration-300 border-0 bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-950/50 dark:to-emerald-950/50 cursor-pointer hover:-translate-y-2">
              <CardHeader>
                <div className="rounded-full bg-green-100 dark:bg-green-900 p-3 w-fit group-hover:scale-110 transition-transform">
                  <Zap className="h-6 w-6 text-green-600 dark:text-green-400" />
                </div>
                <CardTitle className="text-xl group-hover:text-green-600 dark:group-hover:text-green-400 transition-colors">
                  Real-Time Progress Tracking
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-slate-600 dark:text-slate-300 mb-4">
                  Monitor your learning journey with detailed analytics, skill gap analysis, and achievement tracking.
                </p>
                <div className="flex items-center text-green-600 dark:text-green-400 font-medium group-hover:translate-x-2 transition-transform">
                  View Dashboard <ArrowRight className="ml-2 h-4 w-4" />
                </div>
              </CardContent>
            </Card>
          </Link>
        </div>
      </section>

      {/* How It Works */}
      <section className="space-y-12">
        <div className="text-center space-y-4">
          <h2 className="text-3xl md:text-4xl font-bold text-slate-900 dark:text-white">How It Works</h2>
          <p className="text-lg text-slate-600 dark:text-slate-300 max-w-2xl mx-auto">
            Get started in three simple steps
          </p>
        </div>

        <div className="grid gap-8 md:grid-cols-3">
          <div className="text-center space-y-4">
            <div className="rounded-full bg-gradient-to-r from-blue-500 to-purple-500 text-white w-16 h-16 flex items-center justify-center text-2xl font-bold mx-auto">
              1
            </div>
            <h3 className="text-xl font-semibold">Upload & Discover</h3>
            <p className="text-slate-600 dark:text-slate-300">
              Upload your learning materials or take our career assessment to discover your path.
            </p>
          </div>

          <div className="text-center space-y-4">
            <div className="rounded-full bg-gradient-to-r from-purple-500 to-pink-500 text-white w-16 h-16 flex items-center justify-center text-2xl font-bold mx-auto">
              2
            </div>
            <h3 className="text-xl font-semibold">Learn & Practice</h3>
            <p className="text-slate-600 dark:text-slate-300">
              Engage with AI-generated micro-lessons, flashcards, and interactive quizzes.
            </p>
          </div>

          <div className="text-center space-y-4">
            <div className="rounded-full bg-gradient-to-r from-pink-500 to-red-500 text-white w-16 h-16 flex items-center justify-center text-2xl font-bold mx-auto">
              3
            </div>
            <h3 className="text-xl font-semibold">Track & Achieve</h3>
            <p className="text-slate-600 dark:text-slate-300">
              Monitor your progress and achieve your career goals with personalized insights.
            </p>
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section className="space-y-12">
        <div className="text-center space-y-4">
          <h2 className="text-3xl md:text-4xl font-bold text-slate-900 dark:text-white">What Our Users Say</h2>
        </div>

        <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
          <Card className="border-0 bg-white dark:bg-slate-800 shadow-lg">
            <CardContent className="pt-6">
              <div className="flex items-center space-x-1 mb-4">
                {[...Array(5)].map((_, i) => (
                  <Star key={i} className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                ))}
              </div>
              <p className="text-slate-600 dark:text-slate-300 mb-4">
                "TrainPI transformed my learning experience. The micro-lessons are perfect for my busy schedule!"
              </p>
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full flex items-center justify-center text-white font-semibold">
                  S
                </div>
                <div>
                  <div className="font-semibold">Sarah Chen</div>
                  <div className="text-sm text-slate-500">Software Engineer</div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="border-0 bg-white dark:bg-slate-800 shadow-lg">
            <CardContent className="pt-6">
              <div className="flex items-center space-x-1 mb-4">
                {[...Array(5)].map((_, i) => (
                  <Star key={i} className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                ))}
              </div>
              <p className="text-slate-600 dark:text-slate-300 mb-4">
                "The career pathfinder helped me discover opportunities I never knew existed. Highly recommended!"
              </p>
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full flex items-center justify-center text-white font-semibold">
                  M
                </div>
                <div>
                  <div className="font-semibold">Marcus Johnson</div>
                  <div className="text-sm text-slate-500">Data Scientist</div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="border-0 bg-white dark:bg-slate-800 shadow-lg">
            <CardContent className="pt-6">
              <div className="flex items-center space-x-1 mb-4">
                {[...Array(5)].map((_, i) => (
                  <Star key={i} className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                ))}
              </div>
              <p className="text-slate-600 dark:text-slate-300 mb-4">
                "Amazing platform! The progress tracking keeps me motivated and the content is always relevant."
              </p>
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-gradient-to-r from-green-500 to-blue-500 rounded-full flex items-center justify-center text-white font-semibold">
                  A
                </div>
                <div>
                  <div className="font-semibold">Aisha Patel</div>
                  <div className="text-sm text-slate-500">UX Designer</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* CTA Section */}
      <section className="text-center space-y-8 py-20 bg-gradient-to-r from-blue-600 via-purple-600 to-indigo-600 rounded-3xl text-white mx-4">
        <div className="space-y-4">
          <h2 className="text-3xl md:text-4xl font-bold">Ready to Transform Your Career?</h2>
          <p className="text-xl opacity-90 max-w-2xl mx-auto">
            Join thousands of professionals who are already accelerating their growth with TrainPI.
          </p>
        </div>

        <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
          <Link href="/learn">
            <Button
              size="lg"
              variant="secondary"
              className="px-8 py-6 text-lg font-semibold bg-white text-slate-900 hover:bg-slate-100 shadow-lg hover:shadow-xl transition-all duration-300"
            >
              Get Started Free
              <ArrowRight className="ml-2 h-5 w-5" />
            </Button>
          </Link>
          <Link href="/career">
            <Button
              size="lg"
              variant="outline"
              className="px-8 py-6 text-lg font-semibold border-2 border-white text-white hover:bg-white hover:text-slate-900 transition-all duration-300 bg-transparent"
            >
              Explore Features
            </Button>
          </Link>
        </div>

        <div className="flex items-center justify-center space-x-6 pt-8 opacity-90">
          <div className="flex items-center space-x-2">
            <CheckCircle className="h-5 w-5" />
            <span>Free to start</span>
          </div>
          <div className="flex items-center space-x-2">
            <CheckCircle className="h-5 w-5" />
            <span>No credit card required</span>
          </div>
          <div className="flex items-center space-x-2">
            <CheckCircle className="h-5 w-5" />
            <span>Cancel anytime</span>
          </div>
        </div>
      </section>
    </div>
  )
}
