'use client'

import { useEffect, useState, useRef } from 'react'

interface CyberCounterProps {
  value: number
  duration?: number
  decimals?: number
  suffix?: string
  prefix?: string
  className?: string
  glowColor?: 'cyan' | 'blue' | 'purple' | 'green'
}

export function CyberCounter({
  value,
  duration = 1000,
  decimals = 0,
  suffix = '',
  prefix = '',
  className = '',
  glowColor = 'cyan'
}: CyberCounterProps) {
  const [count, setCount] = useState(0)
  const countRef = useRef(0)
  const startTimeRef = useRef<number | null>(null)

  useEffect(() => {
    startTimeRef.current = null
    const animate = (timestamp: number) => {
      if (!startTimeRef.current) startTimeRef.current = timestamp
      const progress = Math.min((timestamp - startTimeRef.current) / duration, 1)

      // Easing function for smooth animation
      const easeOutQuart = 1 - Math.pow(1 - progress, 4)
      const currentCount = easeOutQuart * value

      countRef.current = currentCount
      setCount(currentCount)

      if (progress < 1) {
        requestAnimationFrame(animate)
      }
    }

    requestAnimationFrame(animate)
  }, [value, duration])

  const glowColors = {
    cyan: 'text-cyber-cyan',
    blue: 'text-cyber-blue',
    purple: 'text-cyber-purple',
    green: 'text-cyber-green'
  }

  return (
    <span className={`cyber-number ${glowColors[glowColor]} ${className}`}>
      {prefix}
      {count.toFixed(decimals)}
      {suffix}
    </span>
  )
}
