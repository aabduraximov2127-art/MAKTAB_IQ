import { useEffect, useRef } from "react"

const COLORS = ["#8052ff", "#ffb829", "#15846e", "#c45cff", "#4d7cff", "#ff5c9a", "#b59aff"]

interface Particle {
  x: number // normalised, -1..1 around the shape's centre
  y: number
  size: number
  angle: number
  spin: number
  phase: number
  color: string
  alpha: number
}

/** Point inside a two-lobed, brain-like cloud (rejection sampling). */
function brainPoint(): { x: number; y: number } {
  for (;;) {
    const x = Math.random() * 2 - 1
    const y = Math.random() * 2 - 1
    const lobe = Math.min(Math.hypot(x + 0.3, y * 1.15), Math.hypot(x - 0.3, y * 1.15))
    const fold = 0.06 * Math.sin(x * 14) * Math.cos(y * 11)
    const inside = lobe + fold < 0.66 && !(Math.abs(x) < 0.025 && y < 0.1)
    if (inside) return { x, y }
  }
}

function makeParticles(count: number): Particle[] {
  return Array.from({ length: count }, (_, i) => {
    const ambient = i % 5 === 0
    const p = ambient ? { x: Math.random() * 2 - 1, y: Math.random() * 2 - 1 } : brainPoint()
    return {
      ...p,
      size: ambient ? 2 + Math.random() * 3 : 2.5 + Math.random() * 4,
      angle: Math.random() * Math.PI * 2,
      spin: (Math.random() - 0.5) * 0.008,
      phase: Math.random() * Math.PI * 2,
      color: COLORS[Math.floor(Math.random() * COLORS.length)],
      alpha: ambient ? 0.18 + Math.random() * 0.25 : 0.55 + Math.random() * 0.45,
    }
  })
}

/** Animated field of tiny outlined triangles forming a brain-shaped constellation. */
export function ParticleConstellation({ className = "", count = 1400 }: { className?: string; count?: number }) {
  const ref = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const canvas = ref.current
    if (!canvas) return
    const ctx = canvas.getContext("2d")
    if (!ctx) return

    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches
    const particles = makeParticles(count)
    let w = 0
    let h = 0
    let raf = 0

    const resize = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2)
      w = canvas.clientWidth
      h = canvas.clientHeight
      canvas.width = w * dpr
      canvas.height = h * dpr
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
    }
    resize()
    const ro = new ResizeObserver(() => {
      resize()
      if (reduce) draw(0)
    })
    ro.observe(canvas)

    function draw(t: number) {
      ctx!.clearRect(0, 0, w, h)
      const scale = Math.min(w, h) * 0.5
      const cx = w / 2
      const cy = h / 2
      ctx!.lineWidth = 1
      for (const p of particles) {
        const drift = reduce ? 0 : Math.sin(t / 1800 + p.phase)
        const px = cx + (p.x + drift * 0.012) * scale * 0.9
        const py = cy + (p.y + (reduce ? 0 : Math.cos(t / 2100 + p.phase) * 0.012)) * scale * 0.9
        const a = p.angle + (reduce ? 0 : p.spin * t * 0.06)
        const twinkle = reduce ? 1 : 0.75 + 0.25 * Math.sin(t / 700 + p.phase * 3)
        ctx!.globalAlpha = p.alpha * twinkle
        ctx!.strokeStyle = p.color
        ctx!.beginPath()
        for (let k = 0; k < 3; k++) {
          const ang = a + (k * Math.PI * 2) / 3
          const vx = px + Math.cos(ang) * p.size
          const vy = py + Math.sin(ang) * p.size
          if (k === 0) ctx!.moveTo(vx, vy)
          else ctx!.lineTo(vx, vy)
        }
        ctx!.closePath()
        ctx!.stroke()
      }
      ctx!.globalAlpha = 1
      if (!reduce) raf = requestAnimationFrame(draw)
    }
    raf = requestAnimationFrame(draw)

    return () => {
      cancelAnimationFrame(raf)
      ro.disconnect()
    }
  }, [count])

  return <canvas ref={ref} className={`pointer-events-none block h-full w-full ${className}`} aria-hidden="true" />
}
