import { motion } from 'framer-motion'

interface TrustGaugeProps {
  score: number
  size?: number
}

export function TrustGauge({ score, size = 220 }: TrustGaugeProps) {
  const radius = 86
  const circumference = 2 * Math.PI * radius
  const offset = circumference * (1 - score / 100)
  const color = score >= 80 ? '#10b981' : score >= 60 ? '#f59e0b' : '#f43f5e'

  return (
    <div className="relative grid place-items-center" style={{ width: size, height: size }}>
      <svg viewBox="0 0 220 220" className="h-full w-full -rotate-90">
        <circle cx="110" cy="110" r={radius} fill="none" stroke="rgba(255,255,255,.08)" strokeWidth="18" />
        <motion.circle
          cx="110"
          cy="110"
          r={radius}
          fill="none"
          stroke={color}
          strokeLinecap="round"
          strokeWidth="18"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 0.9, ease: 'easeOut' }}
        />
      </svg>
      <div className="absolute text-center">
        <div className="text-5xl font-semibold text-white">{score}</div>
        <div className="mt-1 text-sm font-medium text-slate-400">Trust score</div>
      </div>
    </div>
  )
}

