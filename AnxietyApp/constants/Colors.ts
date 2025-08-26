// constants/Colors.ts

/**
 * A mapping of light and dark theme colors used throughout the app.
 * You can expand this with any additional semantic colors you need.
 */
export const Colors: Record<'light' | 'dark', { [key: string]: string }> = {
  light: {
    text: '#000000',
    background: '#FFFFFF',
    tint: '#2f95dc',
    tabIconDefault: '#8e8e93',
    tabIconSelected: '#2f95dc',
  },
  dark: {
    text: '#FFFFFF',
    background: '#000000',
    tint: '#fff',
    tabIconDefault: '#8e8e93',
    tabIconSelected: '#fff',
  },
};