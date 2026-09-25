import { t } from "../i18n"
/** Today's date (yyyy-mm-dd) on the local calendar — not UTC, which is a day behind after midnight in UTC+5. */
export function todayISO() {
  const now = new Date()
  return new Date(now.getTime() - now.getTimezoneOffset() * 60000).toISOString().slice(0, 10)
}

export const WEEKDAYS_UZ = [t("Yakshanba"), t("Dushanba"), t("Seshanba"), t("Chorshanba"), t("Payshanba"), t("Juma"), t("Shanba")]

export function weekdayUz(dateStr: string) {
  // parse as a LOCAL date: new Date("2026-09-21") is UTC midnight, the wrong day west of Greenwich
  const [year, month, day] = dateStr.split("-").map(Number)
  return WEEKDAYS_UZ[new Date(year!, (month ?? 1) - 1, day ?? 1).getDay()]
}
