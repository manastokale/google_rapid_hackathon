import { useEffect, useMemo, useState } from 'react'

interface CountUpProps {
  value: number
  formatter?: (value: number) => string
  duration?: number
}

export function CountUp({ value, formatter = (item) => item.toLocaleString(), duration = 700 }: CountUpProps) {
  const [display, setDisplay] = useState(0)
  const stableFormatter = useMemo(() => formatter, [formatter])

  useEffect(() => {
    const started = performance.now()
    let frame = 0
    const tick = (now: number) => {
      const progress = Math.min((now - started) / duration, 1)
      setDisplay(value * (1 - Math.pow(1 - progress, 3)))
      if (progress < 1) {
        frame = requestAnimationFrame(tick)
      }
    }
    frame = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(frame)
  }, [duration, value])

  return <>{stableFormatter(display)}</>
}

