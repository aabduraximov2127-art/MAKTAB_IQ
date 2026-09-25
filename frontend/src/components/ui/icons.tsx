import type { SVGProps } from "react"

/*
 * Material Symbols style filled icons ("Toggle On", "Toggle Off", "Logout"). They follow
 * `currentColor` and the surrounding text size, like the lucide icons used everywhere else.
 */
type IconProps = SVGProps<SVGSVGElement>

function Icon({ d, ...props }: IconProps & { d: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" {...props}>
      <path d={d} />
    </svg>
  )
}

export function ToggleOnIcon(props: IconProps) {
  return (
    <Icon
      d="M17 7H7c-2.76 0-5 2.24-5 5s2.24 5 5 5h10c2.76 0 5-2.24 5-5s-2.24-5-5-5zm0 8c-1.66 0-3-1.34-3-3s1.34-3 3-3 3 1.34 3 3-1.34 3-3 3z"
      {...props}
    />
  )
}

export function ToggleOffIcon(props: IconProps) {
  return (
    <Icon
      d="M17 7H7c-2.76 0-5 2.24-5 5s2.24 5 5 5h10c2.76 0 5-2.24 5-5s-2.24-5-5-5zM7 15c-1.66 0-3-1.34-3-3s1.34-3 3-3 3 1.34 3 3-1.34 3-3 3z"
      {...props}
    />
  )
}

export function LogoutIcon(props: IconProps) {
  return (
    <Icon
      d="M17 7l-1.41 1.41L18.17 11H8v2h10.17l-2.58 2.58L17 17l5-5-5-5zM4 5h8V3H4c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h8v-2H4V5z"
      {...props}
    />
  )
}
