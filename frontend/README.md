# MaktabIQ — Frontend

React + Vite + TypeScript + Tailwind CSS asosida qurilgan, barcha rollarga (SUPERADMIN,
ADMIN, TEACHER, STUDENT, PARENT) moslashuvchan frontend.

## Stack

- React 19 + Vite + TypeScript
- Tailwind CSS v4 (custom design tokens: brand/accent ranglar, dark mode)
- React Router v7
- Zustand (auth, theme, notifications state)
- Axios (JWT access/refresh interceptor)
- Recharts (statistika grafiklari)
- Framer Motion (animatsiyalar)
- Native WebSocket (real-time chat va notification)

## Ishga tushirish

```bash
npm install
npm run dev
```

Dev server `http://localhost:5173` da ishga tushadi va `/api` so'rovlarini
`http://localhost:8000` ga, `/ws` so'rovlarini `ws://localhost:8001` ga proksi qiladi
(`vite.config.ts`). Backend (Django) va Channels/Daphne serveri ishga tushirilgan bo'lishi kerak
— asosiy loyihaning README.md fayliga qarang.

## Build

```bash
npm run build
npm run preview
```

## Struktura

```
src/
  components/
    ui/        # Button, Card, Input, Table, Modal, Drawer, StatCard va h.k.
    layout/    # Sidebar, Topbar, AppLayout, NotificationBell
    shared/    # Sahifalar orasida umumiy bloklar (LessonRow va h.k.)
  pages/       # Har bir marshrut uchun sahifa komponenti
  routes/      # ProtectedRoute, RoleGuard
  store/       # zustand: auth, theme, notifications
  hooks/       # useFetch, useNotificationSocket
  lib/         # api client, formatlash, navigatsiya konfiguratsiyasi
  types/       # backend modellariga mos TypeScript interfeyslar
```

## Rol asosidagi UI

Har bir sahifa `useAuthStore`dagi `user.role`ga qarab turli ko'rinish/ruxsatlarni
ko'rsatadi (masalan `Grades.tsx` — o'qituvchi uchun boshqaruv jadvali, o'quvchi/ota-ona
uchun shaxsiy statistika). Backenddagi permission tekshiruvlari asosiy manba —
frontend faqat UX uchun elementlarni yashiradi/ko'rsatadi.
