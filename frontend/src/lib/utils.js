import { clsx } from "clsx";
import { twMerge } from "tailwind-merge"
import ENV from "@/config/env.config";

// Merge class names with Tailwind Merge
export function cn(...inputs) {
  return twMerge(clsx(inputs));
}

// Debug log
export function debugLog(...args) {
  if (ENV.DEBUG) {
    console.log(...args);
  }
}

// Debug error
export function debugError(...args) {
  if (ENV.DEBUG) {
    console.error(...args);
  }
}

// Debug warning
export function debugWarn(...args) {
  if (ENV.DEBUG) {
    console.warn(...args);
  }
}

// Debug info
export function debugInfo(...args) {
  if (ENV.DEBUG) {
    console.info(...args);
  }
}