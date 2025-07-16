import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { 
  Zap, 
  Mail, 
  Lock, 
  ArrowLeft, 
  User, 
  Settings,
  CheckCircle,
  AlertCircle,
  Loader2
} from 'lucide-react'

const LoginPage = () => {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const navigate = useNavigate()

  const handleQuickLogin = (type) => {
    if (type === 'demo') {
      setEmail('demo@livewire.com')
      setPassword('demo123')
    } else if (type === 'admin') {
      setEmail('admin@livewire.com')
      setPassword('admin123')
    }
    setError('')
    setSuccess(`${type === 'demo' ? 'Demo client' : 'Admin'} credentials loaded. Click "Login to Dashboard" to continue.`)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setIsLoading(true)
    setError('')
    setSuccess('')

    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1500))

      // Demo authentication
      if (email === 'demo@livewire.com' && password === 'demo123') {
        setSuccess('Login successful! Redirecting to dashboard...')
        setTimeout(() => {
          navigate('/dashboard')
        }, 1000)
      } else if (email === 'admin@livewire.com' && password === 'admin123') {
        setSuccess('Admin login successful! Redirecting to admin panel...')
        setTimeout(() => {
          navigate('/admin')
        }, 1000)
      } else {
        setError('Invalid credentials. Try demo@livewire.com / demo123 or admin@livewire.com / admin123')
      }
    } catch (err) {
      setError('Login failed. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
        >
          {/* Header */}
          <div className="text-center mb-8">
            <Link to="/" className="inline-flex items-center space-x-2 mb-6 text-slate-600 hover:text-slate-900 transition-colors">
              <ArrowLeft className="h-4 w-4" />
              <span>Back to Home</span>
            </Link>
            
            <div className="flex items-center justify-center space-x-2 mb-4">
              <div className="bg-gradient-to-r from-blue-600 to-purple-600 p-3 rounded-xl">
                <Zap className="h-8 w-8 text-white" />
              </div>
              <span className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                LiveWire
              </span>
            </div>
            
            <h1 className="text-2xl font-bold text-slate-900 mb-2">Welcome back</h1>
            <p className="text-slate-600">Access your lead generation dashboard</p>
          </div>

          {/* Demo Credentials Card */}
          <Card className="mb-6 bg-gradient-to-r from-green-50 to-emerald-50 border-green-200">
            <CardHeader className="pb-4">
              <CardTitle className="text-lg text-green-800 flex items-center">
                <CheckCircle className="h-5 w-5 mr-2" />
                Demo Access Available
              </CardTitle>
              <CardDescription className="text-green-700">
                Use these credentials to explore the platform
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <Button
                  variant="outline"
                  className="h-auto p-4 flex flex-col items-center space-y-2 border-green-200 hover:bg-green-100"
                  onClick={() => handleQuickLogin('demo')}
                >
                  <User className="h-5 w-5 text-green-600" />
                  <div className="text-center">
                    <div className="font-medium text-green-800">Demo Client</div>
                    <div className="text-xs text-green-600">demo@livewire.com</div>
                    <div className="text-xs text-green-600">demo123</div>
                  </div>
                </Button>
                
                <Button
                  variant="outline"
                  className="h-auto p-4 flex flex-col items-center space-y-2 border-green-200 hover:bg-green-100"
                  onClick={() => handleQuickLogin('admin')}
                >
                  <Settings className="h-5 w-5 text-green-600" />
                  <div className="text-center">
                    <div className="font-medium text-green-800">Admin Panel</div>
                    <div className="text-xs text-green-600">admin@livewire.com</div>
                    <div className="text-xs text-green-600">admin123</div>
                  </div>
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Login Form */}
          <Card className="shadow-2xl border-0 bg-white/80 backdrop-blur-sm">
            <CardHeader className="text-center">
              <CardTitle className="text-xl">Sign in to your account</CardTitle>
              <CardDescription>
                Or use the demo credentials above
              </CardDescription>
            </CardHeader>
            
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-6">
                <div className="space-y-2">
                  <Label htmlFor="email" className="text-sm font-medium text-slate-700">
                    Email Address
                  </Label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
                    <Input
                      id="email"
                      type="email"
                      placeholder="Enter your email address"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className="pl-10 h-12 bg-white border-slate-200 focus:border-blue-500 focus:ring-blue-500"
                      required
                    />
                  </div>
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="password" className="text-sm font-medium text-slate-700">
                    Password
                  </Label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
                    <Input
                      id="password"
                      type="password"
                      placeholder="Enter your password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className="pl-10 h-12 bg-white border-slate-200 focus:border-blue-500 focus:ring-blue-500"
                      required
                    />
                  </div>
                </div>

                {error && (
                  <Alert className="border-red-200 bg-red-50">
                    <AlertCircle className="h-4 w-4 text-red-600" />
                    <AlertDescription className="text-red-700">
                      {error}
                    </AlertDescription>
                  </Alert>
                )}

                {success && (
                  <Alert className="border-green-200 bg-green-50">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                    <AlertDescription className="text-green-700">
                      {success}
                    </AlertDescription>
                  </Alert>
                )}
                
                <Button
                  type="submit"
                  className="w-full h-12 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-medium"
                  disabled={isLoading}
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Signing in...
                    </>
                  ) : (
                    <>
                      <Zap className="h-4 w-4 mr-2" />
                      Login to Dashboard
                    </>
                  )}
                </Button>
              </form>
              
              <div className="mt-6 text-center space-y-4">
                <div className="relative">
                  <div className="absolute inset-0 flex items-center">
                    <div className="w-full border-t border-slate-200" />
                  </div>
                  <div className="relative flex justify-center text-sm">
                    <span className="px-2 bg-white text-slate-500">Need help?</span>
                  </div>
                </div>
                
                <div className="flex justify-center space-x-4 text-sm">
                  <a href="#" className="text-blue-600 hover:text-blue-700 font-medium">
                    Forgot password?
                  </a>
                  <span className="text-slate-300">•</span>
                  <a href="#" className="text-blue-600 hover:text-blue-700 font-medium">
                    Create account
                  </a>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Footer */}
          <div className="mt-8 text-center text-sm text-slate-500">
            <p>
              By signing in, you agree to our{' '}
              <a href="#" className="text-blue-600 hover:text-blue-700">Terms of Service</a>
              {' '}and{' '}
              <a href="#" className="text-blue-600 hover:text-blue-700">Privacy Policy</a>
            </p>
          </div>
        </motion.div>
      </div>
    </div>
  )
}

export default LoginPage

