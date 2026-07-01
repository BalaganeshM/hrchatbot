import { useState } from 'react'
import { useApi } from '../hooks/useApi'
import { api } from '../services/api'
import { Shield, Plus, Pencil, Trash2 } from 'lucide-react'

export default function AdminPanel() {
  const { data: employees, loading, refetch } = useApi(() => api.listEmployees())
  const [showForm, setShowForm] = useState(false)
  const [editing, setEditing] = useState<any>(null)
  const [form, setForm] = useState({ email: '', password: '', first_name: '', last_name: '', role: 'employee', position: '', salary: '', department_id: '', manager_id: '' })

  const resetForm = () => {
    setForm({ email: '', password: '', first_name: '', last_name: '', role: 'employee', position: '', salary: '', department_id: '', manager_id: '' })
    setEditing(null)
    setShowForm(false)
  }

  const handleEdit = (emp: any) => {
    setForm({
      email: emp.email,
      password: '',
      first_name: emp.first_name,
      last_name: emp.last_name,
      role: emp.role,
      position: emp.position || '',
      department_id: emp.department_id || '',
      manager_id: emp.manager_id || '',
    })
    setEditing(emp)
    setShowForm(true)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      if (editing) {
        const payload: any = {}
        if (form.first_name !== editing.first_name) payload.first_name = form.first_name
        if (form.last_name !== editing.last_name) payload.last_name = form.last_name
        if (form.role !== editing.role) payload.role = form.role
        if (form.position !== (editing.position || '')) payload.position = form.position
        await api.updateEmployee(editing.id, payload)
      } else {
        await api.createEmployee({ ...form, salary: parseFloat(form.salary) || null, manager_id: form.manager_id || undefined })
      }
      resetForm()
      refetch()
    } catch (err: any) {
      alert(err.message)
    }
  }

  const handleDelete = async (id: string) => {
    if (!confirm('Deactivate this employee?')) return
    try {
      await api.deleteEmployee(id)
      refetch()
    } catch (err: any) {
      alert(err.message)
    }
  }

  if (loading) return <div className="animate-pulse">Loading...</div>

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6 flex items-center gap-2">
        <Shield className="w-6 h-6 text-red-500" /> Admin Panel
      </h1>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100">
        <div className="p-6 border-b border-gray-100 flex items-center justify-between">
          <h2 className="text-lg font-semibold">Employee Management</h2>
          <button
            onClick={() => { resetForm(); setShowForm(true) }}
            className="flex items-center gap-1.5 px-3 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700"
          >
            <Plus className="w-4 h-4" /> Add Employee
          </button>
        </div>

        {showForm && (
          <form onSubmit={handleSubmit} className="p-6 border-b border-gray-100 bg-gray-50">
            <div className="grid grid-cols-3 gap-4 mb-4">
              <input placeholder="First Name" value={form.first_name} onChange={(e) => setForm({ ...form, first_name: e.target.value })} className="px-3 py-2 border rounded-lg text-sm" required />
              <input placeholder="Last Name" value={form.last_name} onChange={(e) => setForm({ ...form, last_name: e.target.value })} className="px-3 py-2 border rounded-lg text-sm" required />
              <input placeholder="Email" type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} className="px-3 py-2 border rounded-lg text-sm" required={!editing} disabled={!!editing} />
              {!editing && <input placeholder="Password" type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} className="px-3 py-2 border rounded-lg text-sm" required={!editing} />}
              <select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })} className="px-3 py-2 border rounded-lg text-sm">
                <option value="employee">Employee</option>
                <option value="manager">Manager</option>
                <option value="admin">Admin</option>
              </select>
              <input placeholder="Position" value={form.position} onChange={(e) => setForm({ ...form, position: e.target.value })} className="px-3 py-2 border rounded-lg text-sm" />
              {!editing && <input placeholder="Salary" type="number" value={form.salary} onChange={(e) => setForm({ ...form, salary: e.target.value })} className="px-3 py-2 border rounded-lg text-sm" />}
            </div>
            <div className="flex gap-2">
              <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700">
                {editing ? 'Update' : 'Create'}
              </button>
              <button type="button" onClick={resetForm} className="px-4 py-2 border border-gray-300 rounded-lg text-sm hover:bg-gray-100">
                Cancel
              </button>
            </div>
          </form>
        )}

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-100 bg-gray-50">
                <th className="text-left p-4 font-medium text-gray-500">Name</th>
                <th className="text-left p-4 font-medium text-gray-500">Email</th>
                <th className="text-left p-4 font-medium text-gray-500">Role</th>
                <th className="text-left p-4 font-medium text-gray-500">Position</th>
                <th className="text-left p-4 font-medium text-gray-500">Salary</th>
                <th className="text-right p-4 font-medium text-gray-500">Actions</th>
              </tr>
            </thead>
            <tbody>
              {(employees || []).map((emp: any) => (
                <tr key={emp.id} className="border-b border-gray-50 hover:bg-gray-50">
                  <td className="p-4">{emp.full_name}</td>
                  <td className="p-4 text-gray-500">{emp.email}</td>
                  <td className="p-4"><span className={`px-2 py-1 rounded-full text-xs font-medium capitalize ${
                    emp.role === 'admin' ? 'bg-red-100 text-red-700' : emp.role === 'manager' ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-700'
                  }`}>{emp.role}</span></td>
                  <td className="p-4">{emp.position || '-'}</td>
                  <td className="p-4">${emp.salary?.toLocaleString() || '-'}</td>
                  <td className="p-4 text-right">
                    <button onClick={() => handleEdit(emp)} className="p-1.5 text-gray-400 hover:text-blue-600"><Pencil className="w-4 h-4" /></button>
                    <button onClick={() => handleDelete(emp.id)} className="p-1.5 text-gray-400 hover:text-red-600"><Trash2 className="w-4 h-4" /></button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
