// app/DailyCheckIn.tsx

import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Alert,
} from 'react-native';
import { db, auth } from '../firebaseConfig';
import { doc, setDoc, serverTimestamp } from 'firebase/firestore';

export default function DailyCheckIn() {
  const [mood, setMood] = useState('');
  const [notes, setNotes] = useState('');

  const handleSubmit = async () => {
    if (!mood.trim()) {
      Alert.alert('Please enter your mood');
      return;
    }
    try {
      const user = auth.currentUser;
      if (!user) throw new Error('Not signed in');
      await setDoc(doc(db, 'checkins', user.uid + '_' + Date.now()), {
        uid: user.uid,
        mood,
        notes,
        createdAt: serverTimestamp(),
      });
      Alert.alert('Saved', 'Your check-in has been saved.');
      setMood('');
      setNotes('');
    } catch (e: any) {
      Alert.alert('Error', e.message);
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Daily Check-In</Text>

      <Text style={styles.label}>How are you feeling today?</Text>
      <TextInput
        style={styles.input}
        placeholder="E.g., anxious, calm, stressed…"
        value={mood}
        onChangeText={setMood}
      />

      <Text style={styles.label}>Notes (optional)</Text>
      <TextInput
        style={[styles.input, styles.notes]}
        placeholder="Anything on your mind?"
        multiline
        value={notes}
        onChangeText={setNotes}
      />

      <TouchableOpacity style={styles.button} onPress={handleSubmit}>
        <Text style={styles.buttonText}>Submit Check-In</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex:1, padding:24, backgroundColor:'#fff' },
  title:     { fontSize:24, fontWeight:'bold', marginBottom:16 },
  label:     { fontWeight:'600', marginTop:12, marginBottom:4 },
  input:     { borderWidth:1, borderColor:'#ccc', borderRadius:6, padding:12 },
  notes:     { height:100, textAlignVertical:'top' },
  button:    { backgroundColor:'#22a644', padding:14, borderRadius:6, marginTop:24, alignItems:'center' },
  buttonText:{ color:'#fff', fontWeight:'600' },
});