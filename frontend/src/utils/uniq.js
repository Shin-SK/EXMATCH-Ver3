// src/utils/uniq.js
export function uniqById(items, pick = (x) => x) {
  const map = new Map()
  for (const it of items) {
    const v = pick(it)
    if (!v || v.id == null) continue
    if (!map.has(v.id)) map.set(v.id, v)
  }
  return Array.from(map.values())
}
