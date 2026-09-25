/** Lower-case and drop apostrophe variants, so "oqituvchi" also finds "O'qituvchi". */
export function normalise(text: string) {
  return text.toLowerCase().replace(/['`’ʻʼ‘´]/g, "")
}

/** True when any of ``texts`` contains the (already trimmed) query, ignoring case and apostrophes. */
export function matchesQuery(query: string, ...texts: (string | null | undefined)[]) {
  const q = normalise(query.trim())
  if (!q) return true
  return texts.some((text) => !!text && normalise(text).includes(q))
}
