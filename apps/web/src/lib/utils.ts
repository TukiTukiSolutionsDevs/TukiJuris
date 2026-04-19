import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/** Merge Tailwind classes safely — handles conflicts and conditionals. */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
