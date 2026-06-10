import { Menu, ShieldCheck } from 'lucide-react'
import { Outlet } from 'react-router-dom'
import { Sidebar } from './Sidebar'

export function Layout() {
  return (
    <div className="flex min-h-screen text-slate-100">
      <Sidebar />
      <div className="min-w-0 flex-1">
        <header className="sticky top-0 z-20 border-b border-white/10 bg-slate-950/80 backdrop-blur-xl">
          <div className="flex h-16 items-center justify-between px-4 sm:px-6 lg:px-8">
            <div className="flex items-center gap-3 lg:hidden">
              <div className="grid h-9 w-9 place-items-center rounded-lg border border-emerald-400/30 bg-emerald-500/10 text-emerald-200">
                <ShieldCheck className="h-4 w-4" />
              </div>
              <span className="font-semibold text-white">MarginTrust AI</span>
            </div>
            <div className="hidden lg:block">
              <p className="text-sm text-slate-400">Revenue leakage command center</p>
            </div>
            <button className="grid h-9 w-9 place-items-center rounded-md border border-white/10 bg-white/5 text-slate-200 lg:hidden" title="Menu">
              <Menu className="h-4 w-4" />
            </button>
          </div>
        </header>
        <main className="px-4 py-6 sm:px-6 lg:px-8">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

