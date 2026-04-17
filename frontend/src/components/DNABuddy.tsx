import { useEffect, useState, useRef } from 'react'

type MascotState = 'idle' | 'thinking' | 'happy' | 'wave'

interface DNABuddyProps {
  isLoading?: boolean
  hasResults?: boolean
  compact?: boolean
}

export function DNABuddy({ isLoading = false, hasResults = false, compact = false }: DNABuddyProps) {
  const [state, setState] = useState<MascotState>('idle')
  const [blink, setBlink] = useState(false)
  const [wiggle, setWiggle] = useState(false)
  const idleTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // Sync state with loading/results
  useEffect(() => {
    if (isLoading) {
      setState('thinking')
      return
    }
    if (hasResults) {
      setState('happy')
      const t = setTimeout(() => setState('idle'), 2500)
      return () => clearTimeout(t)
    }
    setState('idle')
  }, [isLoading, hasResults])

  // Random blinking
  useEffect(() => {
    const scheduleBlink = () => {
      const delay = 2000 + Math.random() * 4000
      return setTimeout(() => {
        setBlink(true)
        setTimeout(() => setBlink(false), 180)
        idleTimerRef.current = scheduleBlink()
      }, delay)
    }
    idleTimerRef.current = scheduleBlink()
    return () => { if (idleTimerRef.current) clearTimeout(idleTimerRef.current) }
  }, [])

  // Random quirky wiggle
  useEffect(() => {
    const scheduleWiggle = () => setTimeout(() => {
      setWiggle(true)
      setTimeout(() => setWiggle(false), 600)
      scheduleWiggle()
    }, 4000 + Math.random() * 5000)
    const t = scheduleWiggle()
    return () => clearTimeout(t)
  }, [])

  // Eye shapes
  const eyeHeight = blink ? 1 : 6
  const eyeY = blink ? 29 : 26

  // Body transform based on state
  const bodyClass = state === 'thinking'
    ? 'animate-[dna-dance_0.5s_ease-in-out_infinite_alternate]'
    : state === 'happy'
      ? 'animate-[dna-jump_0.4s_ease-in-out_3]'
      : wiggle
        ? 'animate-[dna-wiggle_0.6s_ease-in-out]'
        : 'animate-[dna-bob_3s_ease-in-out_infinite]'

  const leftArmRotate = state === 'thinking' ? -30 : state === 'happy' ? -60 : 0
  const rightArmRotate = state === 'thinking' ? 30 : state === 'happy' ? 60 : 0

  const mouthPath = state === 'happy'
    ? 'M 24 40 Q 28 45 32 40'
    : state === 'thinking'
      ? 'M 24 41 Q 28 41 32 41'
      : 'M 24 40 Q 28 43 32 40'

  return (
    <div className={compact ? 'select-none' : 'flex justify-center mb-1 select-none'} aria-hidden>
      <svg
        width={compact ? 28 : 56}
        height={compact ? 36 : 72}
        viewBox="0 0 56 80"
        className={compact ? '' : bodyClass}
        style={{ overflow: 'visible', transition: 'filter 0.3s' }}
        filter={state === 'happy' ? 'drop-shadow(0 0 6px rgba(255,255,255,0.15))' : undefined}
      >
        {/* ── DNA strand (body / tail) ── */}
        {/* Left strand */}
        <path
          d="M 22 55 C 17 60 19 65 22 68 C 25 71 23 76 18 79"
          stroke={state === 'thinking' ? '#a78bfa' : '#ffffff'}
          strokeWidth="2"
          strokeLinecap="round"
          fill="none"
          opacity="0.4"
        />
        {/* Right strand */}
        <path
          d="M 34 55 C 39 60 37 65 34 68 C 31 71 33 76 38 79"
          stroke={state === 'thinking' ? '#67e8f9' : '#ffffff'}
          strokeWidth="2"
          strokeLinecap="round"
          fill="none"
          opacity="0.4"
        />
        {/* Rungs */}
        {[59, 65, 71].map((y, i) => (
          <line
            key={i}
            x1={i % 2 === 0 ? 20 : 22}
            y1={y}
            x2={i % 2 === 0 ? 36 : 34}
            y2={y}
            stroke="white"
            strokeWidth="1.5"
            strokeLinecap="round"
            opacity="0.2"
          />
        ))}

        {/* ── Left arm ── */}
        <g transform={`translate(20, 36) rotate(${leftArmRotate}) translate(-20, -36)`} style={{ transition: 'transform 0.3s ease' }}>
          <line x1="20" y1="36" x2="9" y2="44" stroke="white" strokeWidth="2.5" strokeLinecap="round" opacity="0.6" />
          {/* Hand */}
          <circle cx="8" cy="45.5" r="2" fill="white" opacity="0.5" />
        </g>

        {/* ── Right arm ── */}
        <g transform={`translate(36, 36) rotate(${rightArmRotate}) translate(-36, -36)`} style={{ transition: 'transform 0.3s ease' }}>
          <line x1="36" y1="36" x2="47" y2="44" stroke="white" strokeWidth="2.5" strokeLinecap="round" opacity="0.6" />
          <circle cx="48" cy="45.5" r="2" fill="white" opacity="0.5" />
        </g>

        {/* ── Body ── */}
        <ellipse cx="28" cy="42" rx="10" ry="8" fill="white" opacity="0.06" />

        {/* ── Head ── */}
        {/* Outer glow ring */}
        <circle
          cx="28"
          cy="24"
          r="18"
          fill="none"
          stroke={state === 'thinking' ? '#a78bfa' : state === 'happy' ? '#86efac' : 'white'}
          strokeWidth="0.5"
          opacity={state !== 'idle' ? 0.25 : 0}
          style={{ transition: 'opacity 0.4s, stroke 0.4s' }}
        />
        {/* Head bg */}
        <circle
          cx="28"
          cy="24"
          r="16"
          fill="#161616"
          stroke="white"
          strokeWidth="1.5"
          opacity="0.9"
        />
        {/* Inner fill */}
        <circle cx="28" cy="24" r="15" fill="#1a1a1a" />

        {/* ── Eyes ── */}
        <rect x="22" y={eyeY} width="4" height={eyeHeight} rx="2" fill="white" opacity="0.85" style={{ transition: 'height 0.1s, y 0.1s' }} />
        <rect x="30" y={eyeY} width="4" height={eyeHeight} rx="2" fill="white" opacity="0.85" style={{ transition: 'height 0.1s, y 0.1s' }} />

        {/* Eye shine */}
        {!blink && <>
          <circle cx="23.5" cy="26.5" r="1" fill="white" opacity="0.5" />
          <circle cx="31.5" cy="26.5" r="1" fill="white" opacity="0.5" />
        </>}

        {/* ── Mouth ── */}
        <path
          d={mouthPath}
          stroke="white"
          strokeWidth="1.8"
          strokeLinecap="round"
          fill="none"
          opacity="0.7"
          style={{ transition: 'd 0.3s' }}
        />

        {/* Thinking swirl when loading */}
        {state === 'thinking' && (
          <g transform="translate(38, 10)">
            <circle cx="0" cy="0" r="5" fill="none" stroke="#a78bfa" strokeWidth="1.5" opacity="0.6" strokeDasharray="8 4">
              <animateTransform
                attributeName="transform"
                attributeType="XML"
                type="rotate"
                from="0 0 0"
                to="360 0 0"
                dur="1.2s"
                repeatCount="indefinite"
              />
            </circle>
            <text x="-3" y="4" fontSize="6" fill="#a78bfa" opacity="0.8">?</text>
          </g>
        )}

        {/* Sparkles when happy */}
        {state === 'happy' && (
          <>
            <text x="40" y="14" fontSize="9" opacity="0.7">✦</text>
            <text x="10" y="12" fontSize="7" opacity="0.6">✦</text>
          </>
        )}
      </svg>

      <style>{`
        @keyframes dna-bob {
          0%, 100% { transform: translateY(0px); }
          50% { transform: translateY(-5px); }
        }
        @keyframes dna-dance {
          0% { transform: translateY(0) rotate(-4deg); }
          100% { transform: translateY(-8px) rotate(4deg); }
        }
        @keyframes dna-jump {
          0%, 100% { transform: translateY(0) scale(1); }
          40% { transform: translateY(-12px) scale(1.05); }
          60% { transform: translateY(-8px) scale(1.02); }
        }
        @keyframes dna-wiggle {
          0%, 100% { transform: rotate(0deg); }
          20% { transform: rotate(-8deg); }
          40% { transform: rotate(8deg); }
          60% { transform: rotate(-5deg); }
          80% { transform: rotate(5deg); }
        }
      `}</style>
    </div>
  )
}
