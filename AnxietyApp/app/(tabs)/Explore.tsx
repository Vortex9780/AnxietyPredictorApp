// app/tabs/Explore.tsx

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

export default function Explore() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Explore</Text>
      <Text>Here you might surface insights, tips, etc.</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex:1, justifyContent:'center', alignItems:'center' },
  title:     { fontSize:24, fontWeight:'bold', marginBottom:8 },
});