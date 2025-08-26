// hooks/useColorScheme.ts

import { useColorScheme as nativeUseColorScheme } from 'react-native';

/**
 * A custom hook that wraps React Native's useColorScheme,
 * guaranteeing a 'light' | 'dark' return value.
 */
export function useColorScheme(): 'light' | 'dark' {
  const scheme = nativeUseColorScheme();
  return scheme === 'dark' ? 'dark' : 'light';
}