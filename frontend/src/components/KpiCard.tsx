import { ReactNode } from 'react'
import { motion } from 'framer-motion'
import { CountUp } from './CountUp'

interface KpiCardProps {
  title: string
  value: number
  icon: ReactNode
  tone: 'emerald' | 'amber' | 'rose' | 'blue' | 'violet'
  formatter?: (value: number) => string
  caption: string
}

const toneMap = {
  emerald: 'text-emerald-300 bg-emerald-500/10 border-emerald-400/20',
  amber: 'text-amber-300 bg-amber-500/10 border-amber-400/20',
  rose: 'text-rose-300 bg-rose-500/10 border-rose-400/20',
  blue: 'text-blue-300 bg-blue-500/10 border-blue-400/20',
  violet: 'text-violet-300 bg-violet-500/10 border-violet-400/20',
}

export function KpiCard({ title, value, icon, tone, formatter, caption }: KpiCardProps) {
  return (
    <motion.article
      whileHover={{ y: -3, scale: 1.01 }}
      className="surface rounded-lg p-4"
    >
      <div className="flex items-start justify-between gap-3">
        <div className={`grid h-10 w-10 shrink-0 place-items-center rounded-lg border ${toneMap[tone]}`}>
          {icon}
        </div>
        <p className="muted text-right text-xs font-medium uppercase tracking-wide">{title}</p>
      </div>
      <div className="mt-4 text-2xl font-semibold text-white">
        <CountUp value={value} formatter={formatter} />
      </div>
      <p className="mt-1 text-sm text-slate-400">{caption}</p>
    </motion.article>
  )
}

