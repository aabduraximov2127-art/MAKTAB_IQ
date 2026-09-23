import { useEffect, useRef } from "react"
import { getTelegram } from "./telegram"

/**
 * Drives Telegram's native bottom MainButton (the chrome Telegram itself renders, outside
 * the webview) instead of drawing our own submit button — the expected pattern for a Mini
 * App's primary action. Shown while `active`, hidden on unmount/when `active` is false.
 */
export function useMainButton({
  text,
  active,
  loading = false,
  onClick,
}: {
  text: string
  active: boolean
  loading?: boolean
  onClick: () => void
}) {
  const onClickRef = useRef(onClick)
  onClickRef.current = onClick

  useEffect(() => {
    const tg = getTelegram()
    if (!tg || !active) return
    const button = tg.MainButton
    const handler = () => onClickRef.current()

    button.setText(text).show().onClick(handler)
    return () => {
      button.offClick(handler)
      button.hide()
    }
  }, [text, active])

  useEffect(() => {
    const tg = getTelegram()
    if (!tg || !active) return
    if (loading) tg.MainButton.showProgress().disable()
    else tg.MainButton.hideProgress().enable()
  }, [loading, active])
}
