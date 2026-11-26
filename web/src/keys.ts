export type ProviderKey = { name: string; label: string; getAt: string; usedFor: string };

export const PROVIDER_KEYS: ProviderKey[] = [
  { name: "ADDIS_API_KEY", label: "Addis AI key", getAt: "https://docs.addisassistant.com/docs/get-started/introduction", usedFor: "Translate (Amharic, Afaan Oromo)" },
  { name: "GEMINI_API_KEY", label: "Gemini API key", getAt: "https://aistudio.google.com/apikey", usedFor: "Voice (free tier)" },
  { name: "CLOUDFLARE_ACCOUNT_ID", label: "Cloudflare account ID", getAt: "https://dash.cloudflare.com/", usedFor: "Pictures (free daily allowance)" },
  { name: "CLOUDFLARE_API_TOKEN", label: "Cloudflare API token", getAt: "https://dash.cloudflare.com/profile/api-tokens", usedFor: "Pictures" },
  { name: "OPENROUTER_API_KEY", label: "OpenRouter key", getAt: "https://openrouter.ai/keys", usedFor: "Motion with Grok Imagine; translation for other languages" },
  { name: "WAVESPEED_API_KEY", label: "WaveSpeed key", getAt: "https://wavespeed.ai/", usedFor: "Music; motion with Wan 2.2" },
];

const STORAGE_KEY = "videomaker.keys";

export function loadSavedKeys(): Record<string, string> {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) ?? "{}");
  } catch {
    return {};
  }
}

export function saveKeys(keys: Record<string, string>, remember: boolean) {
  try {
    if (remember) localStorage.setItem(STORAGE_KEY, JSON.stringify(keys));
    else localStorage.removeItem(STORAGE_KEY);
  } catch {
    // Private windows can block storage; the keys still work for this visit.
  }
}
