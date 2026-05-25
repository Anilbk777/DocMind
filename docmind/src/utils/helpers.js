/** File extension → accent colour */
export const EXT_COLORS = {
  pdf:  '#DF7F83',
  txt:  '#FEBE98',
  md:   '#6b8f5e',
  docx: '#7a9abf',
};
export function extColor(filename) {
  const e = filename.split('.').pop().toLowerCase();
  return EXT_COLORS[e] ?? '#aaa';
}

/** Strip **Sources Gathered:** block from raw LLM output (used during streaming) */
export function stripSources(raw) {
  return raw.replace(/\*\*Sources Gathered:\*\*[\s\S]*/i, '').trim();
}

/** Extract body + sources array from completed LLM output */
export function extractSources(raw) {
  const marker = '**Sources Gathered:**';
  const idx    = raw.indexOf(marker);
  if (idx === -1) return { body: raw.trim(), sources: [] };
  const body    = raw.slice(0, idx).trim();
  const tail    = raw.slice(idx + marker.length);
  const sources = tail
    .split('\n')
    .map(l => l.replace(/^-\s*\*?(.*?)\*?$/, '$1').trim())
    .filter(Boolean);
  return { body, sources };
}
