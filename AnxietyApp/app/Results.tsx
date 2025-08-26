// app/Results.tsx

import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, FlatList } from 'react-native';
import { db, auth } from '../firebaseConfig';
import { collection, query, where, orderBy, getDocs } from 'firebase/firestore';

type CheckIn = { mood: string; notes?: string; createdAt: { toDate(): Date } };

export default function Results() {
  const [data, setData] = useState<CheckIn[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      const user = auth.currentUser;
      if (!user) return;
      const q = query(
        collection(db, 'checkins'),
        where('uid', '==', user.uid),
        orderBy('createdAt', 'desc')
      );
      const snap = await getDocs(q);
      const items: CheckIn[] = snap.docs.map(d => d.data() as any);
      setData(items);
      setLoading(false);
    })();
  }, []);

  if (loading) return <Text style={styles.loading}>Loading…</Text>;

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Your Check-Ins</Text>
      <FlatList
        data={data}
        keyExtractor={(_, i) => i.toString()}
        renderItem={({ item }) => (
          <View style={styles.item}>
            <Text style={styles.date}>
              {item.createdAt.toDate().toLocaleString()}
            </Text>
            <Text style={styles.mood}>Mood: {item.mood}</Text>
            {item.notes ? <Text>Notes: {item.notes}</Text> : null}
          </View>
        )}
        ListEmptyComponent={<Text>No entries yet.</Text>}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex:1, padding:24 },
  title:     { fontSize:24, fontWeight:'bold', marginBottom:16 },
  loading:   { padding:24, textAlign:'center' },
  item:      { padding:12, borderBottomWidth:1, borderColor:'#eee' },
  date:      { fontSize:12, color:'#666' },
  mood:      { fontWeight:'600' },
});