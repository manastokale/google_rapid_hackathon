import { BarChart3, Bot, DatabaseZap, ListChecks, ShieldCheck } from 'lucide-react'
import { NavLink } from 'react-router-dom'

const nav = [
  { to: '/', label: 'Dashboard', icon: BarChart3 },
  { to: '/chat', label: 'Agent', icon: Bot },
  { to: '/actions', label: 'Actions', icon: ListChecks },
  { to: '/connectors', label: 'Connectors', icon: DatabaseZap },
]

export function Sidebar() {
  return (
    <aside className="hidden w-64 shrink-0 border-r border-white/10 bg-slate-950/70 p-5 lg:block">
      <div className="flex items-center gap-3">
        <div className="grid h-10 w-10 place-items-center rounded-lg border border-emerald-400/30 bg-emerald-500/10 text-emerald-200">
          <ShieldCheck className="h-5 w-5" />
        </div>
        <div>
          <div className="font-semibold text-white">MarginTrust AI</div>
          <div className="text-xs text-slate-400">StreamWorks Cloud</div>
        </div>
      </div>
      <nav className="mt-8 space-y-2">
        {nav.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition ${
                isActive ? 'bg-white/10 text-white' : 'text-slate-400 hover:bg-white/5 hover:text-white'
              }`
            }
          >
            <Icon className="h-4 w-4" />
            {label}
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}

