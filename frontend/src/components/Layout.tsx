import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { LayoutDashboard, Users, Network, MessageSquareText, LogOut, Shield, Building2 } from 'lucide-react'
import ChatPage from '../pages/ChatPage'

const navItems = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/org', label: 'Org Structure', icon: Network },
  { path: '/chat', label: 'AI Chat', icon: MessageSquareText },
]

const adminItems = [
  { path: '/admin', label: 'Admin Panel', icon: Shield },
]

export default function Layout({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const isChatPage = location.pathname === '/chat'

  const visibleNavItems = user?.role === 'admin' ? navItems.filter(item => item.path !== '/org') : navItems
  const allItems = user?.role === 'admin' ? [...visibleNavItems, ...adminItems] : navItems

  return (
    <div className="flex h-screen bg-gray-50">
      <aside className="w-64 bg-white border-r border-gray-200 flex flex-col">
        <div className="p-6 border-b border-gray-200">
          <h1 className="text-xl font-bold flex items-center gap-2">
            <Building2 className="w-6 h-6 text-blue-600" />
            SCB HRChatBot
          </h1>
          <p className="text-sm text-gray-500 mt-1 capitalize">{user?.role}</p>
        </div>

        <nav className="flex-1 p-4 space-y-1">
          {allItems.map((item) => {
            const Icon = item.icon
            const isActive = location.pathname === item.path
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-blue-50 text-blue-700'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                <Icon className="w-5 h-5" />
                {item.label}
              </Link>
            )
          })}
        </nav>

        <div className="p-4 border-t border-gray-200">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white text-sm font-medium">
              {user?.first_name[0]}{user?.last_name[0]}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">{user?.full_name}</p>
              <p className="text-xs text-gray-500 truncate">{user?.email}</p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="flex items-center gap-2 text-sm text-gray-600 hover:text-red-600 w-full px-3 py-2 rounded-lg hover:bg-red-50 transition-colors"
          >
            <LogOut className="w-4 h-4" /> Logout
          </button>
        </div>
      </aside>

      <main className="flex-1 overflow-auto">
        <div className={`p-8 ${isChatPage ? 'hidden' : ''}`}>{children}</div>
        <div className={`p-8 ${isChatPage ? '' : 'hidden'}`}><ChatPage /></div>
      </main>
    </div>
  )
}
