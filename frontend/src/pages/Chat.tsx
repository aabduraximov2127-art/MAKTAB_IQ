import { type FormEvent, useEffect, useMemo, useRef, useState } from "react"
import { ArrowLeft, MessagesSquare, Pencil, School, Search, Send, Users } from "lucide-react"
import toast from "react-hot-toast"
import { useFetch } from "../hooks/useFetch"
import { api, getErrorMessage } from "../lib/api"
import { useAuthStore } from "../store/auth"
import { Avatar } from "../components/ui/Avatar"
import { Button } from "../components/ui/Button"
import { EmptyState } from "../components/ui/EmptyState"
import { Input } from "../components/ui/Input"
import { Modal } from "../components/ui/Modal"
import { Skeleton } from "../components/ui/Skeleton"
import { cn } from "../lib/cn"
import { formatRelative, fullName } from "../lib/format"
import type { ChatRoom, Message, Paginated, ParentProfile, StudentProfile } from "../types"

const ROOM_TYPE_LABEL: Record<ChatRoom["room_type"], string> = {
  CLASS_GENERAL: "Sinf chati",
  PRIVATE: "Shaxsiy",
  TEACHER_STUDENT: "O'qituvchi-o'quvchi",
  PARENT_TEACHER: "Ota-ona-o'qituvchi",
}

export default function ChatPage() {
  const user = useAuthStore((s) => s.user)
  const canMessageParent = user?.role === "ADMIN" || user?.role === "SUPERADMIN"
  const isStudent = user?.role === "STUDENT"
  const { data: rooms, loading, refetch } = useFetch<Paginated<ChatRoom>>("/chat/?page_size=100")
  const [activeRoom, setActiveRoom] = useState<ChatRoom | null>(null)
  const [mobileThread, setMobileThread] = useState(false)
  const [newMessageOpen, setNewMessageOpen] = useState(false)
  const [joiningClassGroup, setJoiningClassGroup] = useState(false)

  function openRoom(room: ChatRoom) {
    setActiveRoom(room)
    setMobileThread(true)
  }

  async function openClassGroup() {
    setJoiningClassGroup(true)
    try {
      const { data: room } = await api.get<ChatRoom>("/chat/class_group/")
      refetch()
      openRoom(room)
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setJoiningClassGroup(false)
    }
  }

  return (
    <div className="flex h-[calc(100vh-8rem)] overflow-hidden rounded-2xl border border-ink-100 bg-white shadow-soft dark:border-ink-800 dark:bg-ink-900">
      <div className={cn("w-full shrink-0 border-r border-ink-100 dark:border-ink-800 sm:w-80", mobileThread && "hidden sm:block")}>
        <div className="flex items-center justify-between border-b border-ink-100 px-4 py-4 dark:border-ink-800">
          <h2 className="font-display text-lg font-bold text-ink-900 dark:text-white">Chat</h2>
          <div className="flex items-center gap-1">
            {isStudent && (
              <button
                onClick={openClassGroup}
                disabled={joiningClassGroup}
                title="Sinf chatiga o'tish"
                className="flex h-8 w-8 items-center justify-center rounded-lg text-brand-600 transition-colors hover:bg-brand-50 disabled:opacity-60 dark:text-brand-400 dark:hover:bg-brand-500/10"
              >
                <School className="h-4 w-4" />
              </button>
            )}
            {(canMessageParent || isStudent) && (
              <button
                onClick={() => setNewMessageOpen(true)}
                title={isStudent ? "Sinfdoshga yozish" : "Ota-onaga yozish"}
                className="flex h-8 w-8 items-center justify-center rounded-lg text-brand-600 transition-colors hover:bg-brand-50 dark:text-brand-400 dark:hover:bg-brand-500/10"
              >
                <Pencil className="h-4 w-4" />
              </button>
            )}
          </div>
        </div>
        <div className="h-[calc(100%-4rem)] overflow-y-auto">
          {loading ? (
            <div className="space-y-2 p-3">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-14 w-full" />
              ))}
            </div>
          ) : !rooms || rooms.results.length === 0 ? (
            <div className="p-4">
              <EmptyState icon={MessagesSquare} title="Chat mavjud emas" />
            </div>
          ) : (
            rooms.results.map((room) => (
              <button
                key={room.id}
                onClick={() => openRoom(room)}
                className={cn(
                  "flex w-full items-center gap-3 border-b border-ink-50 px-4 py-3.5 text-left transition-colors last:border-0 dark:border-ink-800/60",
                  activeRoom?.id === room.id ? "bg-brand-50 dark:bg-brand-500/10" : "hover:bg-ink-50 dark:hover:bg-ink-800/40"
                )}
              >
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-brand-500 to-brand-700 text-white">
                  <Users className="h-4.5 w-4.5" />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-semibold text-ink-800 dark:text-ink-100">
                    {room.name || ROOM_TYPE_LABEL[room.room_type]}
                  </p>
                  <p className="truncate text-xs text-ink-400">
                    {room.last_message ? room.last_message.text : "Xabar yo'q"}
                  </p>
                </div>
              </button>
            ))
          )}
        </div>
      </div>

      <div className={cn("flex flex-1 flex-col", !mobileThread && "hidden sm:flex")}>
        {activeRoom ? (
          <ChatThread room={activeRoom} onBack={() => setMobileThread(false)} />
        ) : (
          <div className="flex flex-1 items-center justify-center">
            <EmptyState icon={MessagesSquare} title="Suhbatni tanlang" description="Chap tomondan chatlardan birini tanlang" />
          </div>
        )}
      </div>

      {canMessageParent && (
        <NewParentMessageModal
          open={newMessageOpen}
          onClose={() => setNewMessageOpen(false)}
          existingRooms={rooms?.results ?? []}
          onOpened={(room) => {
            setNewMessageOpen(false)
            refetch()
            openRoom(room)
          }}
        />
      )}
      {isStudent && (
        <NewClassmateMessageModal
          open={newMessageOpen}
          onClose={() => setNewMessageOpen(false)}
          existingRooms={rooms?.results ?? []}
          onOpened={(room) => {
            setNewMessageOpen(false)
            refetch()
            openRoom(room)
          }}
        />
      )}
    </div>
  )
}

function NewClassmateMessageModal({
  open,
  onClose,
  existingRooms,
  onOpened,
}: {
  open: boolean
  onClose: () => void
  existingRooms: ChatRoom[]
  onOpened: (room: ChatRoom) => void
}) {
  const user = useAuthStore((s) => s.user)
  const [search, setSearch] = useState("")
  const [startingId, setStartingId] = useState<number | null>(null)

  const { data: me } = useFetch<StudentProfile>(open ? "/students/me/" : null, [open])

  const query = new URLSearchParams({ page_size: "50" })
  if (me?.class_room) query.set("class_room", String(me.class_room))
  if (search) query.set("search", search)
  const { data: classmates, loading } = useFetch<Paginated<StudentProfile>>(
    open && me?.class_room ? `/students/?${query.toString()}` : null,
    [open, me?.class_room, search]
  )

  const others = (classmates?.results ?? []).filter((s) => s.user.id !== user?.id)

  async function startConversation(classmate: StudentProfile) {
    setStartingId(classmate.id)
    try {
      const existing = existingRooms.find(
        (r) => r.room_type === "PRIVATE" && r.members.length === 2 && r.members.some((m) => m.user === classmate.user.id)
      )
      if (existing) {
        onOpened(existing)
        return
      }
      const { data: room } = await api.post<ChatRoom>("/chat/", {
        room_type: "PRIVATE",
        name: fullName(classmate.user),
      })
      await api.post(`/chat/${room.id}/add_member/`, { user: classmate.user.id })
      onOpened(room)
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setStartingId(null)
    }
  }

  return (
    <Modal open={open} onClose={onClose} title="Sinfdoshga yozish">
      <div className="space-y-4">
        <Input
          icon={<Search className="h-4 w-4" />}
          placeholder="Sinfdosh ismi bo'yicha qidirish..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          autoFocus
        />
        <div className="max-h-80 space-y-1.5 overflow-y-auto">
          {loading ? (
            <Skeleton className="h-40 w-full" />
          ) : others.length === 0 ? (
            <EmptyState title="Sinfdosh topilmadi" />
          ) : (
            others.map((s) => (
              <button
                key={s.id}
                onClick={() => startConversation(s)}
                disabled={startingId === s.id}
                className="flex w-full items-center gap-3 rounded-xl border border-ink-100 p-3 text-left transition-colors hover:border-brand-200 hover:bg-brand-50/50 disabled:opacity-60 dark:border-ink-800 dark:hover:border-brand-500/40 dark:hover:bg-brand-500/5"
              >
                <Avatar name={fullName(s.user)} size="sm" />
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium text-ink-800 dark:text-ink-100">{fullName(s.user)}</p>
                  <p className="truncate text-xs text-ink-400">{s.class_room_name ?? ""}</p>
                </div>
                {startingId === s.id && <Button size="sm" loading />}
              </button>
            ))
          )}
        </div>
      </div>
    </Modal>
  )
}

function NewParentMessageModal({
  open,
  onClose,
  existingRooms,
  onOpened,
}: {
  open: boolean
  onClose: () => void
  existingRooms: ChatRoom[]
  onOpened: (room: ChatRoom) => void
}) {
  const [search, setSearch] = useState("")
  const [startingId, setStartingId] = useState<number | null>(null)

  const query = new URLSearchParams({ page_size: "20" })
  if (search) query.set("search", search)
  const { data: parents, loading } = useFetch<Paginated<ParentProfile>>(open ? `/parents/?${query.toString()}` : null, [
    open,
    search,
  ])

  async function startConversation(parent: ParentProfile) {
    setStartingId(parent.id)
    try {
      const existing = existingRooms.find(
        (r) => r.room_type === "PRIVATE" && r.members.length === 2 && r.members.some((m) => m.user === parent.user.id)
      )
      if (existing) {
        onOpened(existing)
        return
      }
      const { data: room } = await api.post<ChatRoom>("/chat/", {
        room_type: "PRIVATE",
        name: fullName(parent.user),
      })
      await api.post(`/chat/${room.id}/add_member/`, { user: parent.user.id })
      onOpened(room)
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setStartingId(null)
    }
  }

  return (
    <Modal open={open} onClose={onClose} title="Ota-onaga yozish">
      <div className="space-y-4">
        <Input
          icon={<Search className="h-4 w-4" />}
          placeholder="Ota-ona ismi bo'yicha qidirish..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          autoFocus
        />
        <div className="max-h-80 space-y-1.5 overflow-y-auto">
          {loading ? (
            <Skeleton className="h-40 w-full" />
          ) : !parents || parents.results.length === 0 ? (
            <EmptyState title="Ota-ona topilmadi" />
          ) : (
            parents.results.map((p) => (
              <button
                key={p.id}
                onClick={() => startConversation(p)}
                disabled={startingId === p.id}
                className="flex w-full items-center gap-3 rounded-xl border border-ink-100 p-3 text-left transition-colors hover:border-brand-200 hover:bg-brand-50/50 disabled:opacity-60 dark:border-ink-800 dark:hover:border-brand-500/40 dark:hover:bg-brand-500/5"
              >
                <Avatar name={fullName(p.user)} size="sm" />
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium text-ink-800 dark:text-ink-100">{fullName(p.user)}</p>
                  <p className="truncate text-xs text-ink-400">
                    {p.children.map((c) => fullName(c.user)).join(", ") || "Farzand biriktirilmagan"}
                  </p>
                </div>
                {startingId === p.id && <Button size="sm" loading />}
              </button>
            ))
          )}
        </div>
      </div>
    </Modal>
  )
}

function ChatThread({ room, onBack }: { room: ChatRoom; onBack: () => void }) {
  const user = useAuthStore((s) => s.user)
  const accessToken = useAuthStore((s) => s.accessToken)
  const [messages, setMessages] = useState<Message[]>([])
  const [text, setText] = useState("")
  const [loading, setLoading] = useState(true)
  const socketRef = useRef<WebSocket | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    setLoading(true)
    api
      .get<Paginated<Message>>(`/chat/messages/?chat_room=${room.id}&page_size=200`)
      .then((res) => setMessages(res.data.results))
      .finally(() => setLoading(false))
  }, [room.id])

  useEffect(() => {
    if (!accessToken) return
    const protocol = window.location.protocol === "https:" ? "wss" : "ws"
    const socket = new WebSocket(`${protocol}://${window.location.host}/ws/chat/${room.id}/?token=${accessToken}`)
    socketRef.current = socket

    socket.onmessage = (event) => {
      const payload = JSON.parse(event.data) as Message
      setMessages((prev) => (prev.some((m) => m.id === payload.id) ? prev : [...prev, payload]))
    }

    return () => socket.close()
  }, [room.id, accessToken])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  function handleSend(e: FormEvent) {
    e.preventDefault()
    const trimmed = text.trim()
    if (!trimmed || socketRef.current?.readyState !== WebSocket.OPEN) return
    socketRef.current.send(JSON.stringify({ text: trimmed }))
    setText("")
  }

  const grouped = useMemo(() => messages, [messages])

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center gap-3 border-b border-ink-100 px-4 py-3.5 dark:border-ink-800">
        <button onClick={onBack} className="rounded-lg p-1.5 text-ink-400 hover:bg-ink-100 dark:hover:bg-ink-800 sm:hidden">
          <ArrowLeft className="h-4.5 w-4.5" />
        </button>
        <div className="flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-br from-brand-500 to-brand-700 text-white">
          <Users className="h-4 w-4" />
        </div>
        <div>
          <p className="text-sm font-semibold text-ink-800 dark:text-ink-100">{room.name || ROOM_TYPE_LABEL[room.room_type]}</p>
          <p className="text-xs text-ink-400">{room.members.length} a'zo</p>
        </div>
      </div>

      <div className="flex-1 space-y-3 overflow-y-auto p-4">
        {loading ? (
          Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-12 w-2/3" />)
        ) : grouped.length === 0 ? (
          <EmptyState title="Xabar yo'q" description="Birinchi xabarni yuboring" />
        ) : (
          grouped.map((m) => {
            const mine = m.sender === user?.id
            return (
              <div key={m.id} className={cn("flex items-end gap-2", mine && "flex-row-reverse")}>
                {!mine && <Avatar name={m.sender_name} size="sm" />}
                <div
                  className={cn(
                    "max-w-[75%] rounded-2xl px-3.5 py-2.5 text-sm",
                    mine
                      ? "rounded-br-sm bg-brand-600 text-white"
                      : "rounded-bl-sm bg-ink-100 text-ink-800 dark:bg-ink-800 dark:text-ink-100"
                  )}
                >
                  {!mine && <p className="mb-0.5 text-xs font-semibold text-brand-500">{m.sender_name}</p>}
                  <p>{m.text}</p>
                  <p className={cn("mt-1 text-[10px]", mine ? "text-brand-100" : "text-ink-400")}>{formatRelative(m.created_at)}</p>
                </div>
              </div>
            )
          })
        )}
        <div ref={bottomRef} />
      </div>

      <form onSubmit={handleSend} className="flex items-center gap-2 border-t border-ink-100 p-3 dark:border-ink-800">
        <input
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Xabar yozing..."
          className="h-11 flex-1 rounded-xl border border-ink-200 bg-white px-3.5 text-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/40 dark:border-ink-700 dark:bg-ink-900 dark:text-white"
        />
        <button
          type="submit"
          className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-brand-600 text-white transition-colors hover:bg-brand-700 disabled:opacity-50"
          disabled={!text.trim()}
        >
          <Send className="h-4.5 w-4.5" />
        </button>
      </form>
    </div>
  )
}
