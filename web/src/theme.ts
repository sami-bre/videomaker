const darkQuery = window.matchMedia("(prefers-color-scheme: dark)");

export function followSystemTheme() {
  const apply = () => document.documentElement.classList.toggle("dark", darkQuery.matches);
  apply();
  darkQuery.addEventListener("change", apply);
}
