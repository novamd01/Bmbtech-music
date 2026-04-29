"use client"

import type React from "react"
import { createContext, useContext, useEffect, useState, type ReactNode } from "react"

type Theme = "light" | "dark" | "system"

interface ThemeContextType {
  theme: Theme
  setTheme: (theme: Theme) => void
  isDark: boolean
}

const ThemeCtx = createContext<ThemeContextType | undefined>(undefined)

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<Theme>("dark")
  const [isDark, setIsDark] = useState(true)
  const [isMounted, setIsMounted] = useState(false)

  // Load theme from localStorage on mount
  useEffect(() => {
    if (typeof window === "undefined") return

    try {
      const saved = localStorage.getItem("musicana_theme") as Theme | null
      const initialTheme: Theme = saved || "dark"
      setThemeState(initialTheme)
      applyTheme(initialTheme)
      setIsMounted(true)
    } catch {
      setThemeState("dark")
      applyTheme("dark")
      setIsMounted(true)
    }
  }, [])

  // Listen for system theme changes
  useEffect(() => {
    if (typeof window === "undefined") return
    if (!isMounted) return

    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)")
    
    const handleChange = (e: MediaQueryListEvent) => {
      if (theme === "system") {
        setIsDark(e.matches)
        updateDocumentTheme(e.matches)
      }
    }

    mediaQuery.addEventListener("change", handleChange)
    return () => mediaQuery.removeEventListener("change", handleChange)
  }, [theme, isMounted])

  const applyTheme = (newTheme: Theme) => {
    if (typeof window === "undefined") return

    let shouldBeDark = newTheme === "dark"

    if (newTheme === "system") {
      shouldBeDark = window.matchMedia("(prefers-color-scheme: dark)").matches
    }

    setIsDark(shouldBeDark)
    updateDocumentTheme(shouldBeDark)

    try {
      localStorage.setItem("musicana_theme", newTheme)
    } catch {}
  }

  const updateDocumentTheme = (dark: boolean) => {
    if (typeof document === "undefined") return

    const html = document.documentElement
    if (dark) {
      html.classList.add("dark")
      html.style.colorScheme = "dark"
    } else {
      html.classList.remove("dark")
      html.style.colorScheme = "light"
    }
  }

  const setTheme = (newTheme: Theme) => {
    setThemeState(newTheme)
    applyTheme(newTheme)
  }

  if (!isMounted) {
    return <>{children}</>
  }

  return (
    <ThemeCtx.Provider value={{ theme, setTheme, isDark }}>
      {children}
    </ThemeCtx.Provider>
  )
}

export function useTheme() {
  const ctx = useContext(ThemeCtx)
  if (!ctx) throw new Error("useTheme must be used within a ThemeProvider")
  return ctx
}
