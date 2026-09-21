export function todayISO() {
  return new Date().toISOString().slice(0, 10)
}

export const WEEKDAYS_UZ = ["Yakshanba", "Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba"]

export function weekdayUz(dateStr: string) {
  return WEEKDAYS_UZ[new Date(dateStr).getDay()]
}
