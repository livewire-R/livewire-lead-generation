import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { 
  Zap, 
  Users, 
  Star, 
  Calendar, 
  DollarSign,
  TrendingUp,
  TrendingDown,
  Home,
  LogOut,
  Sparkles,
  Target,
  Download,
  Settings,
  BarChart3,
  Mail,
  Phone,
  Eye,
  MessageCircle
} from 'lucide-react'

const DashboardPage = () => {
  const [stats, setStats] = useState({
    totalLeads: 1247,
    avgScore: 83,
    weeklyLeads: 47,
    costPerLead: 0.07
  })

  const [isGenerating, setIsGenerating] = useState(false)

  const recentLeads = [
    {
      name: "Sarah Johnson",
      company: "Wellness Solutions Australia",
      title: "Director",
      email: "sarah.j@wellness-au.com",
      phone: "+61 2 9876 5432",
      score: 92,
      time: "2 hours ago"
    },
    {
      name: "Michael Chen",
      company: "TechStart Melbourne",
      title: "CEO",
      email: "m.chen@techstart.com.au",
      phone: "+61 3 8765 4321",
      score: 88,
      time: "4 hours ago"
    },
    {
      name: "Emma Wilson",
      company: "Corporate Health Sydney",
      title: "Manager",
      email: "e.wilson@corphealth.com.au",
      phone: "+61 2 7654 3210",
      score: 76,
      time: "6 hours ago"
    },
    {
      name: "James Mitchell",
      company: "Leadership Coaching Brisbane",
      title: "Senior Consultant",
      email: "james@leadership-bne.com",
      phone: "+61 7 5432 1098",
      score: 84,
      time: "8 hours ago"
    },
    {
      name: "Lisa Thompson",
      company: "Business Growth Partners",
      title: "Partner",
      email: "lisa.t@bgpartners.com.au",
      phone: "+61 8 3456 7890",
      score: 91,
      time: "1 day ago"
    }
  ]

  const handleGenerateLeads = async () => {
    setIsGenerating(true)
    
    // Simulate lead generation process
    setTimeout(() => {
      setStats(prev => ({
        ...prev,
        totalLeads: prev.totalLeads + 47,
        weeklyLeads: prev.weeklyLeads + 47
      }))
      setIsGenerating(false)
    }, 3000)
  }

  const getScoreColor = (score) => {
    if (score >= 85) return 'bg-green-500'
    if (score >= 70) return 'bg-yellow-500'
    return 'bg-red-500'
  }

  const getScoreBadgeColor = (score) => {
    if (score >= 85) return 'bg-green-100 text-green-700'
    if (score >= 70) return 'bg-yellow-100 text-yellow-700'
    return 'bg-red-100 text-red-700'
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <div className="bg-gradient-to-r from-blue-600 to-purple-600 p-2 rounded-lg">
                  <Zap className="h-6 w-6 text-white" />
                </div>
                <span className="text-xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                  LiveWire Dashboard
                </span>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full flex items-center justify-center text-white font-semibold text-sm">
                  DC
                </div>
                <div className="hidden sm:block">
                  <div className="text-sm font-medium text-slate-900">Demo Client</div>
                  <div className="text-xs text-slate-500">Professional Plan</div>
                </div>
              </div>
              
              <div className="flex items-center space-x-2">
                <Link to="/">
                  <Button variant="outline" size="sm">
                    <Home className="h-4 w-4 mr-2" />
                    Home
                  </Button>
                </Link>
                <Link to="/login">
                  <Button variant="outline" size="sm">
                    <LogOut className="h-4 w-4 mr-2" />
                    Logout
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <Card className="bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-blue-700">Total Leads Generated</CardTitle>
                <Users className="h-4 w-4 text-blue-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-blue-900">{stats.totalLeads.toLocaleString()}</div>
                <div className="flex items-center text-xs text-blue-600 mt-1">
                  <TrendingUp className="h-3 w-3 mr-1" />
                  +12% from last month
                </div>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
          >
            <Card className="bg-gradient-to-br from-purple-50 to-purple-100 border-purple-200">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-purple-700">Average Lead Score</CardTitle>
                <Star className="h-4 w-4 text-purple-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-purple-900">{stats.avgScore}</div>
                <div className="flex items-center text-xs text-purple-600 mt-1">
                  <TrendingUp className="h-3 w-3 mr-1" />
                  +5% from last week
                </div>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
          >
            <Card className="bg-gradient-to-br from-green-50 to-green-100 border-green-200">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-green-700">Leads This Week</CardTitle>
                <Calendar className="h-4 w-4 text-green-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-green-900">{stats.weeklyLeads}</div>
                <div className="flex items-center text-xs text-green-600 mt-1">
                  <TrendingUp className="h-3 w-3 mr-1" />
                  +8% from last week
                </div>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
          >
            <Card className="bg-gradient-to-br from-orange-50 to-orange-100 border-orange-200">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-orange-700">Cost Per Lead</CardTitle>
                <DollarSign className="h-4 w-4 text-orange-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-orange-900">${stats.costPerLead}</div>
                <div className="flex items-center text-xs text-red-600 mt-1">
                  <TrendingDown className="h-3 w-3 mr-1" />
                  -2% from last month
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </div>

        {/* Lead Generation Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.4 }}
          className="mb-8"
        >
          <Card className="bg-gradient-to-br from-slate-50 to-white border-slate-200 shadow-lg">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-2xl font-bold text-slate-900 flex items-center">
                    <Sparkles className="h-6 w-6 mr-2 text-blue-600" />
                    Lead Generation
                  </CardTitle>
                  <CardDescription className="text-slate-600 mt-2">
                    Generate new high-quality leads for your business using our AI-powered system with Apollo.io integration.
                  </CardDescription>
                </div>
                <Badge className="bg-green-100 text-green-700">
                  <Target className="h-4 w-4 mr-1" />
                  Active
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center p-4 bg-blue-50 rounded-lg">
                  <div className="text-2xl font-bold text-blue-700">2.3k</div>
                  <div className="text-sm text-blue-600">This Month</div>
                </div>
                <div className="text-center p-4 bg-green-50 rounded-lg">
                  <div className="text-2xl font-bold text-green-700">95%</div>
                  <div className="text-sm text-green-600">Email Accuracy</div>
                </div>
                <div className="text-center p-4 bg-purple-50 rounded-lg">
                  <div className="text-2xl font-bold text-purple-700">2.1s</div>
                  <div className="text-sm text-purple-600">Avg Response Time</div>
                </div>
                <div className="text-center p-4 bg-orange-50 rounded-lg">
                  <div className="text-2xl font-bold text-orange-700">24/7</div>
                  <div className="text-sm text-orange-600">Automated</div>
                </div>
              </div>
              
              <div className="flex flex-col sm:flex-row gap-4">
                <Button
                  onClick={handleGenerateLeads}
                  disabled={isGenerating}
                  className="bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 flex-1"
                  size="lg"
                >
                  {isGenerating ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Generating 50 Leads...
                    </>
                  ) : (
                    <>
                      <Sparkles className="h-4 w-4 mr-2" />
                      Generate 50 Leads
                    </>
                  )}
                </Button>
                <Button variant="outline" size="lg" className="flex-1">
                  <Settings className="h-4 w-4 mr-2" />
                  Custom Generation
                </Button>
                <Button variant="outline" size="lg" className="flex-1">
                  <Download className="h-4 w-4 mr-2" />
                  Export All Leads
                </Button>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Recent Leads Table */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.5 }}
        >
          <Card className="bg-white border-slate-200 shadow-lg">
            <CardHeader>
              <CardTitle className="text-xl font-bold text-slate-900 flex items-center">
                <BarChart3 className="h-5 w-5 mr-2 text-blue-600" />
                Recent Leads
              </CardTitle>
              <CardDescription>
                Your latest generated leads with AI-powered quality scores and contact information.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-slate-200">
                      <th className="text-left py-3 px-4 font-medium text-slate-700">Contact</th>
                      <th className="text-left py-3 px-4 font-medium text-slate-700">Company</th>
                      <th className="text-left py-3 px-4 font-medium text-slate-700">Contact Info</th>
                      <th className="text-left py-3 px-4 font-medium text-slate-700">Score</th>
                      <th className="text-left py-3 px-4 font-medium text-slate-700">Generated</th>
                      <th className="text-left py-3 px-4 font-medium text-slate-700">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {recentLeads.map((lead, index) => (
                      <motion.tr
                        key={index}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ duration: 0.3, delay: index * 0.1 }}
                        className="border-b border-slate-100 hover:bg-slate-50 transition-colors"
                      >
                        <td className="py-4 px-4">
                          <div>
                            <div className="font-medium text-slate-900">{lead.name}</div>
                            <div className="text-sm text-slate-600">{lead.title}</div>
                          </div>
                        </td>
                        <td className="py-4 px-4">
                          <div className="text-slate-900">{lead.company}</div>
                        </td>
                        <td className="py-4 px-4">
                          <div className="space-y-1">
                            <div className="flex items-center text-sm text-slate-600">
                              <Mail className="h-3 w-3 mr-1" />
                              {lead.email}
                            </div>
                            <div className="flex items-center text-sm text-slate-600">
                              <Phone className="h-3 w-3 mr-1" />
                              {lead.phone}
                            </div>
                          </div>
                        </td>
                        <td className="py-4 px-4">
                          <Badge className={getScoreBadgeColor(lead.score)}>
                            {lead.score}
                          </Badge>
                        </td>
                        <td className="py-4 px-4">
                          <div className="text-sm text-slate-600">{lead.time}</div>
                        </td>
                        <td className="py-4 px-4">
                          <div className="flex space-x-2">
                            <Button size="sm" variant="outline">
                              <Eye className="h-3 w-3 mr-1" />
                              View
                            </Button>
                            <Button size="sm" className="bg-green-600 hover:bg-green-700">
                              <MessageCircle className="h-3 w-3 mr-1" />
                              Contact
                            </Button>
                          </div>
                        </td>
                      </motion.tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  )
}

export default DashboardPage

