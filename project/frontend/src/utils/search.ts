import type { Event } from "../types/Event";

function normalize(s: string): string {
  return s.toLowerCase().replace(/\s+/g, " ").trim();
}

// Splits query into tokens (space-separated) and phrases ("...")
function parseQuery(q: string): { tokens: string[]; phrases: string[] } {
  const raw = q.trim();
  if (!raw) return { tokens: [], phrases: [] };

  const phrases: string[] = [];
  let remaining = raw;

  // Extract quoted phrases: "foo bar"
  remaining = remaining.replace(/"([^"]+)"/g, (_, phrase) => {
    phrases.push(normalize(phrase));
    return " ";
  });

  const tokens = remaining
    .split(/\s+/)
    .map(normalize)
    .filter(Boolean);

  return { tokens, phrases };
}

function eventToHaystack(e: Event): string {
  return normalize(
    [
      e.title,
      e.description,
      e.location,
      e.speaker,
      e.organizer,
      e.url,
      e.city,
      e.country,
    ]
      .filter(Boolean)
      .join(" ")
  );
}

// AND semantics: every token and phrase must appear somewhere
export function matchesEvent(e: Event, q: string): boolean {
  const { tokens, phrases } = parseQuery(q);
  if (tokens.length === 0 && phrases.length === 0) return true;

  const hay = eventToHaystack(e);

  for (const t of tokens) {
    if (!hay.includes(t)) return false;
  }
  for (const ph of phrases) {
    if (!hay.includes(ph)) return false;
  }

  return true;
}
