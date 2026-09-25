import { type ReactNode, useEffect, useState } from "react"
import { Button } from "./Button"

interface ConfirmButtonProps {
  label: ReactNode
  /** Shown after the first click — the second click really does it. */
  confirmLabel: ReactNode
  onConfirm: () => void | Promise<void>
  icon?: ReactNode
  disabled?: boolean
  loading?: boolean
  className?: string
}

/** A destructive action behind two clicks: the first arms it (the button turns red and asks),
 * the second confirms. It disarms itself after a few seconds. */
export function ConfirmButton({ label, confirmLabel, onConfirm, icon, disabled, loading, className }: ConfirmButtonProps) {
  const [armed, setArmed] = useState(false)

  useEffect(() => {
    if (!armed) return
    const timer = setTimeout(() => setArmed(false), 4000)
    return () => clearTimeout(timer)
  }, [armed])

  return (
    <Button
      type="button"
      variant={armed ? "danger" : "outline"}
      className={className}
      disabled={disabled}
      loading={loading}
      onClick={() => {
        if (!armed) {
          setArmed(true)
          return
        }
        setArmed(false)
        void onConfirm()
      }}
    >
      {icon}
      {armed ? confirmLabel : label}
    </Button>
  )
}
