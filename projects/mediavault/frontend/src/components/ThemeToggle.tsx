import { useEffect, useState } from "react";
import { Icon } from "../lib/icons";

const THEME_KEY = "mv_theme";

export function applyStoredTheme() {
  const stored = localStorage.getItem(THEME_KEY);
  if (stored) document.documentElement.setAttribute("data-theme", stored);
}

export function ThemeToggle() {
  const [theme, setTheme] = useState<string>(
    () => localStorage.getItem(THEME_KEY) || "light",
  );

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem(THEME_KEY, theme);
  }, [theme]);

  return (
    <button
      className="btn btn-ghost btn-sm"
      onClick={() => setTheme((t) => (t === "dark" ? "light" : "dark"))}
      aria-label="Toggle theme"
      title="Toggle theme"
    >
      {theme === "dark" ? <Icon.Sun size={17} /> : <Icon.Moon size={17} />}
    </button>
  );
}
