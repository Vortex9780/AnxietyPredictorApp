// app/(tabs)/home.tsx
import React from 'react';
import { StyleSheet, Text, View } from 'react-native';

export default function HomeScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Home Tab</Text>
      <Text>Welcome to your post-login landing screen.</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 16 },
  title:     { fontSize: 24, fontWeight: 'bold', marginBottom: 8 },
});