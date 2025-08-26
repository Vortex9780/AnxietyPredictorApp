// components/ui/TabBarBackground.tsx
import React from 'react'
import { View, StyleSheet, Platform } from 'react-native'

/**
 * A no-op transparent background on web/Android, but still
 * a valid React component so the tab navigator can render it.
 */
export default function TabBarBackground() {
  return <View style={styles.background} />
}

export function useBottomTabOverflow(): number {
  return 0
}

const styles = StyleSheet.create({
  background: {
    flex: 1,
    backgroundColor: Platform.select({ web: 'transparent', default: 'white' }),
  },
})