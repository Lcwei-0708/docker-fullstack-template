import React, { createContext, useContext, useEffect, useState } from 'react';

const ThemeContext = createContext();

export const THEMES = {
  LIGHT: 'light',
  DARK: 'dark'
};

const THEME_STORAGE_KEY = 'app-theme';
const getSystemTheme = () => {
  if (typeof window !== 'undefined' && window.matchMedia) {
    return window.matchMedia('(prefers-color-scheme: dark)').matches 
      ? THEMES.DARK 
      : THEMES.LIGHT;
  }
  return THEMES.LIGHT;
};

const getStoredTheme = () => {
  if (typeof window !== 'undefined') {
    try {
      const storedTheme = localStorage.getItem(THEME_STORAGE_KEY);
      if (storedTheme && Object.values(THEMES).includes(storedTheme)) {
        return storedTheme;
      }
    } catch (error) {
      console.warn('Failed to read theme from localStorage:', error);
    }
  }
  return null;
};

const setStoredTheme = (theme) => {
  if (typeof window !== 'undefined') {
    try {
      localStorage.setItem(THEME_STORAGE_KEY, theme);
    } catch (error) {
      console.warn('Failed to save theme to localStorage:', error);
    }
  }
};

export const ThemeProvider = ({ children }) => {
  const [theme, setTheme] = useState(() => {
    return getStoredTheme() || getSystemTheme();
  });

  const toggleTheme = () => {
    const newTheme = theme === THEMES.LIGHT ? THEMES.DARK : THEMES.LIGHT;
    setTheme(newTheme);
  };

  const setSpecificTheme = (newTheme) => {
    if (Object.values(THEMES).includes(newTheme)) {
      setTheme(newTheme);
    }
  };

  useEffect(() => {
    setStoredTheme(theme);
    
    if (typeof document !== 'undefined') {
      document.documentElement.classList.toggle('dark', theme === THEMES.DARK);
    }
  }, [theme]);

  useEffect(() => {
    if (typeof window === 'undefined' || !window.matchMedia) return;

    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    
    const handleSystemThemeChange = (e) => {
      if (!getStoredTheme()) {
        const systemTheme = e.matches ? THEMES.DARK : THEMES.LIGHT;
        setTheme(systemTheme);
      }
    };

    mediaQuery.addEventListener('change', handleSystemThemeChange);
    
    return () => {
      mediaQuery.removeEventListener('change', handleSystemThemeChange);
    };
  }, []);

  const contextValue = {
    theme,
    isDark: theme === THEMES.DARK,
    isLight: theme === THEMES.LIGHT,
    toggleTheme,
    setTheme: setSpecificTheme,
    themes: THEMES
  };

  return (
    <ThemeContext.Provider value={contextValue}>
      {children}
    </ThemeContext.Provider>
  );
};

// Hook for using theme
export const useTheme = () => {
  const context = useContext(ThemeContext);
  
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  
  return context;
};

export default ThemeContext;