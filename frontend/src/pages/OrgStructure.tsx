import { useApi } from '../hooks/useApi'
import { api } from '../services/api'
import { useAuth } from '../contexts/AuthContext'
import { Building2, Shield, ChevronDown, ChevronRight } from 'lucide-react'
import { useState, useEffect } from 'react'

const roleColors: Record<string, string> = {
  admin: 'bg-red-100 text-red-600 border-red-200',
  manager: 'bg-blue-100 text-blue-600 border-blue-200',
  employee: 'bg-gray-100 text-gray-600 border-gray-200',
}

const roleStyles: Record<string, string> = {
  admin: 'border-red-400 bg-red-50',
  manager: 'border-blue-400 bg-blue-50',
  employee: 'border-gray-300 bg-white',
}

export default function OrgStructure() {
  const { user } = useAuth()
  const { data: org, loading, refetch: refetchOrg } = useApi(() => api.getOrgStructure())
  const { data: myChain, refetch: refetchChain } = useApi(() => api.getMyChain())

  useEffect(() => {
    const onFocus = () => { refetchOrg(); refetchChain() }
    window.addEventListener('focus', onFocus)
    return () => window.removeEventListener('focus', onFocus)
  }, [refetchOrg, refetchChain])

  if (user?.role === 'admin') {
    return (
      <div>
        <h1 className="text-2xl font-bold mb-6">Organization Structure</h1>
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-12 text-center text-gray-400">
          <Building2 className="w-12 h-12 mx-auto mb-3" />
          <p className="text-lg">Organization chart is not available for admin users.</p>
          <p className="text-sm mt-1">Please use the Admin Panel to manage employees.</p>
        </div>
      </div>
    )
  }

  let treeRoots: any[] = []
  let treeData: any[] = org || []

  if (user?.role === 'manager' && org) {
    const userEntry = org.find((e: any) => e.id === user.id)
    if (userEntry) {
      const teamIds = new Set<string>()
      const collect = (empId: string) => {
        teamIds.add(empId)
        org.filter((e: any) => e.manager_id === empId).forEach((e: any) => collect(e.id))
      }
      collect(userEntry.id)
      treeData = org.filter((e: any) => teamIds.has(e.id))
      treeRoots = treeData.filter((e: any) => e.id === userEntry.id)
    }
  } else if (user?.role === 'employee' && org) {
    const userEntry = org.find((e: any) => e.id === user.id)
    if (userEntry && userEntry.manager_id) {
      const managerEntry = org.find((e: any) => e.id === userEntry.manager_id)
      if (managerEntry) {
        const teamIds = new Set<string>()
        const collect = (empId: string) => {
          teamIds.add(empId)
          org.filter((e: any) => e.manager_id === empId).forEach((e: any) => collect(e.id))
        }
        collect(managerEntry.id)
        treeData = org.filter((e: any) => teamIds.has(e.id))
        treeRoots = treeData.filter((e: any) => e.id === managerEntry.id)
      }
    }
  } else {
    treeRoots = org?.filter((e: any) => !e.manager_id) || []
  }

  if (loading) return <div className="animate-pulse">Loading...</div>

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Organization Structure</h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Building2 className="w-5 h-5 text-blue-600" /> Organization Chart
            </h2>
            {treeRoots.length === 0 ? (
              <div className="text-center py-8 text-gray-400">
                <p>No organization data available for your role.</p>
              </div>
            ) : (
              <div className="overflow-x-auto pb-4">
                <div className="flex flex-col items-center min-w-max">
                  {treeRoots.map((emp: any) => (
                    <OrgNode key={emp.id} emp={emp} all={treeData} depth={0} currentUserId={user?.id} />
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="space-y-4">
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Shield className="w-5 h-5 text-blue-600" /> My Reporting Chain
            </h2>
            {myChain && myChain.length > 0 ? (
              <div className="space-y-2">
                {myChain.map((mgr: any) => (
                  <div key={mgr.id} className="flex items-center gap-3 p-3 bg-blue-50 rounded-lg border border-blue-100">
                    <div className="w-9 h-9 rounded-full bg-blue-600 flex items-center justify-center text-white text-sm font-bold">
                      {mgr.full_name[0]}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-semibold text-blue-900 truncate">{mgr.full_name}</p>
                      <p className="text-xs text-blue-600">{mgr.position}</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex flex-col items-center py-6 text-gray-400">
                <Shield className="w-10 h-10 mb-2" />
                <p className="text-sm">You are at the top of your reporting chain.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

function OrgNode({ emp, all, depth, currentUserId }: { emp: any; all: any[]; depth: number; currentUserId?: string }) {
  const reports = all.filter((e: any) => e.manager_id === emp.id)
  const [open, setOpen] = useState(depth < 2)
  const isCurrentUser = emp.id === currentUserId

  return (
    <div className="flex flex-col items-center">
      <div
        className={`flex items-center gap-3 px-4 py-3 border-2 rounded-xl cursor-pointer hover:shadow-md transition-all min-w-[260px] ${
          isCurrentUser ? 'border-blue-500 bg-blue-50 ring-2 ring-blue-200' : roleStyles[emp.role] || roleStyles.employee
        }`}
        onClick={() => setOpen(!open)}
      >
        <div className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold border-2 ${roleColors[emp.role] || roleColors.employee}`}>
          {emp.full_name[0]}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <p className="text-sm font-semibold text-gray-900 truncate">{emp.full_name}</p>
            <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-gray-100 text-gray-500 capitalize">{emp.role}</span>
          </div>
          <p className="text-xs text-gray-500 truncate">{emp.position || 'N/A'}</p>
          <p className="text-xs text-gray-400 truncate">{emp.department_name}</p>
        </div>
        {reports.length > 0 && (
          <span className="text-gray-400 flex-shrink-0">
            {open ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
          </span>
        )}
      </div>

      {open && reports.length > 0 && (
        <div className="flex flex-col items-center pt-1">
          <div className="w-px h-4 bg-gray-300" />

          <div className="flex gap-6 relative">
            <div className="absolute top-0 left-[10%] right-[10%] h-px bg-gray-300" />

            {reports.map((r: any) => (
              <div key={r.id} className="flex flex-col items-center relative pt-3">
                <div className="absolute top-0 w-px h-3 bg-gray-300" />
                <OrgNode emp={r} all={all} depth={depth + 1} currentUserId={currentUserId} />
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
