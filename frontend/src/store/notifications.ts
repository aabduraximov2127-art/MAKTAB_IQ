import { create } from "zustand"
import type { Notification } from "../types"

interface NotificationState {
  items: Notification[]
  unread: number
  setAll: (items: Notification[]) => void
  prepend: (item: Notification) => void
  markRead: (id: number) => void
  markAllRead: () => void
}

export const useNotificationStore = create<NotificationState>((set) => ({
  items: [],
  unread: 0,
  setAll: (items) => set({ items, unread: items.filter((n) => !n.is_read).length }),
  prepend: (item) => set((s) => ({ items: [item, ...s.items].slice(0, 30), unread: s.unread + 1 })),
  markRead: (id) =>
    set((s) => ({
      items: s.items.map((n) => (n.id === id ? { ...n, is_read: true } : n)),
      unread: Math.max(0, s.unread - (s.items.find((n) => n.id === id && !n.is_read) ? 1 : 0)),
    })),
  markAllRead: () => set((s) => ({ items: s.items.map((n) => ({ ...n, is_read: true })), unread: 0 })),
}))
