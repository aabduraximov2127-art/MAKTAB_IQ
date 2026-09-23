import { t } from "../i18n"
export function todayISO() {
  return new Date().toISOString().slice(0, 10)
}

export const WEEKDAYS_UZ = [t("Yakshanba"), t("Dushanba"), t("Seshanba"), t("Chorshanba"), t("Payshanba"), t("Juma"), t("Shanba")]

export function weekdayUz(dateStr: string) {
  return WEEKDAYS_UZ[new Date(dateStr).getDay()]
}
