import { useAuth } from '../contexts/AuthContext'
import { useApi } from '../hooks/useApi'
import { api } from '../services/api'
import { Users, UserCheck, Building2, Briefcase, UserCircle, BadgeInfo } from 'lucide-react'

export default function Dashboard() {
  const { user } = useAuth()
  const { data: employees } = useApi(() => api.listEmployees())
  const { data: org } = useApi(() => api.getOrgStructure())

  const isAdmin = user?.role === 'admin'
  const isManager = user?.role === 'manager'
  const isNotAdmin = !isAdmin

  const myOrgEntry = org?.find((e: any) => e.id === user?.id) || null
  const departmentName = myOrgEntry?.department_name || null
  const myManagerEntry = org?.find((e: any) => e.id === user?.manager_id) || null

  const myTeamCount = isManager
    ? org?.filter((e: any) => e.manager_id === user?.id)?.length || 0
    : org?.filter((e: any) => e.manager_id === user?.manager_id)?.length || 0

  const formatDate = (d: string | null | undefined) => {
    if (!d) return 'N/A'
    return new Date(d).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Welcome back, {user?.first_name}!</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {isAdmin && (
          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-blue-50 rounded-lg"><Users className="w-6 h-6 text-blue-600" /></div>
              <div className="min-w-0">
                <p className="text-sm text-gray-500">Total Employees</p>
                <p className="text-2xl font-bold">{employees?.length || 0}</p>
              </div>
            </div>
          </div>
        )}
        {isNotAdmin && (
          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-green-50 rounded-lg"><UserCheck className="w-6 h-6 text-green-600" /></div>
              <div className="min-w-0">
                <p className="text-sm text-gray-500">My Team</p>
                <p className="text-2xl font-bold">{myTeamCount}</p>
              </div>
            </div>
          </div>
        )}
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-purple-50 rounded-lg"><Building2 className="w-6 h-6 text-purple-600" /></div>
            <div className="min-w-0">
              <p className="text-sm text-gray-500">Department</p>
              <p className="text-lg font-bold truncate">{departmentName || 'N/A'}</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-amber-50 rounded-lg"><Briefcase className="w-6 h-6 text-amber-600" /></div>
            <div className="min-w-0">
              <p className="text-sm text-gray-500">Position</p>
              <p className="text-lg font-bold break-words">{user?.position || 'N/A'}</p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <div className="bg-white rounded-xl shadow-sm border border-gray-100">
          <div className="p-6 border-b border-gray-100">
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <UserCircle className="w-5 h-5 text-blue-600" /> Personal Information
            </h2>
          </div>
          <div className="p-6 grid grid-cols-2 gap-y-4 gap-x-8 text-sm">
            <div>
              <span className="text-gray-400 text-xs uppercase tracking-wider">Full Name</span>
              <p className="font-medium mt-0.5">{user?.full_name}</p>
            </div>
            <div>
              <span className="text-gray-400 text-xs uppercase tracking-wider">Role</span>
              <p className="font-medium mt-0.5 capitalize">{user?.role}</p>
            </div>
            <div>
              <span className="text-gray-400 text-xs uppercase tracking-wider">Email</span>
              <p className="font-medium mt-0.5 break-all">{user?.email}</p>
            </div>
            <div>
              <span className="text-gray-400 text-xs uppercase tracking-wider">Phone</span>
              <p className="font-medium mt-0.5">{user?.phone || 'N/A'}</p>
            </div>
            <div>
              <span className="text-gray-400 text-xs uppercase tracking-wider">Position</span>
              <p className="font-medium mt-0.5">{user?.position || 'N/A'}</p>
            </div>
            <div>
              <span className="text-gray-400 text-xs uppercase tracking-wider">Department</span>
              <p className="font-medium mt-0.5">{departmentName || 'N/A'}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-100">
          <div className="p-6 border-b border-gray-100">
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <BadgeInfo className="w-5 h-5 text-blue-600" /> Employment Details
            </h2>
          </div>
          <div className="p-6 grid grid-cols-2 gap-y-4 gap-x-8 text-sm">
            <div>
              <span className="text-gray-400 text-xs uppercase tracking-wider">Manager</span>
              <p className="font-medium mt-0.5">{myManagerEntry?.full_name || 'N/A'}</p>
            </div>
            <div>
              <span className="text-gray-400 text-xs uppercase tracking-wider">Status</span>
              <p className="font-medium mt-0.5">
                <span className={`inline-flex items-center gap-1 ${user?.is_active ? 'text-green-600' : 'text-red-500'}`}>
                  <span className={`w-2 h-2 rounded-full ${user?.is_active ? 'bg-green-500' : 'bg-red-500'}`} />
                  {user?.is_active ? 'Active' : 'Inactive'}
                </span>
              </p>
            </div>
            <div>
              <span className="text-gray-400 text-xs uppercase tracking-wider">Hire Date</span>
              <p className="font-medium mt-0.5">{formatDate(user?.hire_date)}</p>
            </div>
            <div>
              <span className="text-gray-400 text-xs uppercase tracking-wider">Account Created</span>
              <p className="font-medium mt-0.5">{formatDate(user?.created_at)}</p>
            </div>
            {isAdmin && (
              <div>
                <span className="text-gray-400 text-xs uppercase tracking-wider">Salary</span>
                <p className="font-medium mt-0.5">{user?.salary ? `$${user.salary.toLocaleString()}` : 'N/A'}</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
