import { useState } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { 
  Zap, 
  Users, 
  Settings, 
  BarChart3, 
  Shield,
  Home,
  LogOut,
  Plus,
  Download,
  Eye,
  Edit,
  Trash2,
  Crown,
  Activity,
  Database,
  Server
} from 'lucide-react'

const AdminPage = () => {
  const [clients] = useState([
    {
      id: 1,
      name: "Demo Client",
      email: "demo@livewire.com",
      plan: "Professional",
      status: "Active",
      leads: 1247,
      lastActive: "2 hours ago"
    },
    {
      id: 2,
      name: "Wellness Solutions Australia",
      email: "admin@wellness-au.com",
      plan: "Enterprise",
      status: "Active",
      leads: 3421,
      lastActive: "1 day ago"
    },
    {
      id: 3,
      name: "TechStart Melbourne",
      email: "contact@techstart.com.au",
      plan: "Starter",
      status: "Active",
      leads: 892,
      lastActive: "3 hours ago"
    },
    {
      id: 4,
      name: "Corporate Health Sydney",
      email: "info@corphealth.com.au",
      plan: "Professional",
      status: "Inactive",
      leads: 567,
      lastActive: "1 week ago"
    }
  ])

  const systemStats = {
    totalClients: 47,
    activeClients: 42,
    totalLeads: 125847,
    systemUptime: "99.99%",
    apiCalls: 2847291,
    revenue: 18750
  }

  const getPlanColor = (plan) => {
    switch (plan) {
      case 'Enterprise': return 'bg-purple-100 text-purple-700'
      case 'Professional': return 'bg-blue-100 text-blue-700'
      case 'Starter': return 'bg-green-100 text-green-700'
      default: return 'bg-gray-100 text-gray-700'
    }
  }

  const getStatusColor = (status) => {
    return status === 'Active' 
      ? 'bg-green-100 text-green-700' 
      : 'bg-red-100 text-red-700'
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-gradient-to-r from-slate-900 to-slate-800 text-white sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <div className="bg-gradient-to-r from-yellow-500 to-orange-500 p-2 rounded-lg">
                  <Crown className="h-6 w-6 text-white" />
                </div>
                <span className="text-xl font-bold">
                  LiveWire Admin Panel
                </span>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-gradient-to-r from-yellow-500 to-orange-500 rounded-full flex items-center justify-center text-white font-semibold text-sm">
                  AD
                </div>
                <div className="hidden sm:block">
                  <div className="text-sm font-medium">Admin User</div>
                  <div className="text-xs text-slate-300">System Administrator</div>
                </div>
              </div>
              
              <div className="flex items-center space-x-2">
                <Link to="/">
                  <Button variant="outline" size="sm" className="border-slate-600 text-slate-300 hover:bg-slate-700">
                    <Home className="h-4 w-4 mr-2" />
                    Home
                  </Button>
                </Link>
                <Link to="/login">
                  <Button variant="outline" size="sm" className="border-slate-600 text-slate-300 hover:bg-slate-700">
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
        {/* System Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <Card className="bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-blue-700">Total Clients</CardTitle>
                <Users className="h-4 w-4 text-blue-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-blue-900">{systemStats.totalClients}</div>
                <div className="text-xs text-blue-600 mt-1">
                  {systemStats.activeClients} active clients
                </div>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
          >
            <Card className="bg-gradient-to-br from-green-50 to-green-100 border-green-200">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-green-700">Total Leads Generated</CardTitle>
                <BarChart3 className="h-4 w-4 text-green-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-green-900">{systemStats.totalLeads.toLocaleString()}</div>
                <div className="text-xs text-green-600 mt-1">
                  Across all clients
                </div>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
          >
            <Card className="bg-gradient-to-br from-purple-50 to-purple-100 border-purple-200">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-purple-700">Monthly Revenue</CardTitle>
                <Activity className="h-4 w-4 text-purple-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-purple-900">${systemStats.revenue.toLocaleString()}</div>
                <div className="text-xs text-purple-600 mt-1">
                  +15% from last month
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
                <CardTitle className="text-sm font-medium text-orange-700">System Uptime</CardTitle>
                <Server className="h-4 w-4 text-orange-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-orange-900">{systemStats.systemUptime}</div>
                <div className="text-xs text-orange-600 mt-1">
                  Last 30 days
                </div>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.4 }}
          >
            <Card className="bg-gradient-to-br from-red-50 to-red-100 border-red-200">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-red-700">API Calls</CardTitle>
                <Database className="h-4 w-4 text-red-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-red-900">{systemStats.apiCalls.toLocaleString()}</div>
                <div className="text-xs text-red-600 mt-1">
                  This month
                </div>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.5 }}
          >
            <Card className="bg-gradient-to-br from-slate-50 to-slate-100 border-slate-200">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-slate-700">System Health</CardTitle>
                <Shield className="h-4 w-4 text-slate-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-green-700">Healthy</div>
                <div className="text-xs text-slate-600 mt-1">
                  All systems operational
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </div>

        {/* Admin Actions */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.6 }}
          className="mb-8"
        >
          <Card className="bg-gradient-to-br from-slate-50 to-white border-slate-200 shadow-lg">
            <CardHeader>
              <CardTitle className="text-2xl font-bold text-slate-900 flex items-center">
                <Settings className="h-6 w-6 mr-2 text-slate-600" />
                System Administration
              </CardTitle>
              <CardDescription className="text-slate-600">
                Manage clients, monitor system performance, and configure platform settings.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex flex-col sm:flex-row gap-4">
                <Button className="bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 flex-1">
                  <Plus className="h-4 w-4 mr-2" />
                  Add New Client
                </Button>
                <Button variant="outline" className="flex-1">
                  <Download className="h-4 w-4 mr-2" />
                  Export System Data
                </Button>
                <Button variant="outline" className="flex-1">
                  <Settings className="h-4 w-4 mr-2" />
                  System Settings
                </Button>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Client Management Table */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.7 }}
        >
          <Card className="bg-white border-slate-200 shadow-lg">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-xl font-bold text-slate-900 flex items-center">
                    <Users className="h-5 w-5 mr-2 text-slate-600" />
                    Client Management
                  </CardTitle>
                  <CardDescription>
                    Monitor and manage all client accounts and their lead generation activities.
                  </CardDescription>
                </div>
                <Button className="bg-gradient-to-r from-green-600 to-green-700">
                  <Plus className="h-4 w-4 mr-2" />
                  Add Client
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-slate-200">
                      <th className="text-left py-3 px-4 font-medium text-slate-700">Client</th>
                      <th className="text-left py-3 px-4 font-medium text-slate-700">Plan</th>
                      <th className="text-left py-3 px-4 font-medium text-slate-700">Status</th>
                      <th className="text-left py-3 px-4 font-medium text-slate-700">Total Leads</th>
                      <th className="text-left py-3 px-4 font-medium text-slate-700">Last Active</th>
                      <th className="text-left py-3 px-4 font-medium text-slate-700">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {clients.map((client, index) => (
                      <motion.tr
                        key={client.id}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ duration: 0.3, delay: index * 0.1 }}
                        className="border-b border-slate-100 hover:bg-slate-50 transition-colors"
                      >
                        <td className="py-4 px-4">
                          <div>
                            <div className="font-medium text-slate-900">{client.name}</div>
                            <div className="text-sm text-slate-600">{client.email}</div>
                          </div>
                        </td>
                        <td className="py-4 px-4">
                          <Badge className={getPlanColor(client.plan)}>
                            {client.plan}
                          </Badge>
                        </td>
                        <td className="py-4 px-4">
                          <Badge className={getStatusColor(client.status)}>
                            {client.status}
                          </Badge>
                        </td>
                        <td className="py-4 px-4">
                          <div className="font-medium text-slate-900">{client.leads.toLocaleString()}</div>
                        </td>
                        <td className="py-4 px-4">
                          <div className="text-sm text-slate-600">{client.lastActive}</div>
                        </td>
                        <td className="py-4 px-4">
                          <div className="flex space-x-2">
                            <Button size="sm" variant="outline">
                              <Eye className="h-3 w-3 mr-1" />
                              View
                            </Button>
                            <Button size="sm" variant="outline">
                              <Edit className="h-3 w-3 mr-1" />
                              Edit
                            </Button>
                            <Button size="sm" variant="outline" className="text-red-600 hover:text-red-700">
                              <Trash2 className="h-3 w-3 mr-1" />
                              Delete
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

export default AdminPage

