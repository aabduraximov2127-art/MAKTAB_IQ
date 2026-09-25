/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Full desktop site URL, opened via the "To'liq saytni ochish" link. Omit to hide it. */
  readonly VITE_FULL_SITE_URL?: string
  /** Absolute API base, e.g. https://maktabiq-api.onrender.com/api/v1 */
  readonly VITE_API_URL?: string
}
