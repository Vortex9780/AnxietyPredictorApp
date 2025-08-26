// firebaseConfig.ts
import { initializeApp }  from 'firebase/app';
import { getFirestore }   from 'firebase/firestore';

// export your config!
export const firebaseConfig = {
  apiKey:       "AIzaSy…",
  authDomain:   "anxietypredictor-43c43.firebaseapp.com",
  projectId:    "anxietypredictor-43c43",
  storageBucket:"anxietypredictor-43c43.firebasestorage.app",
  messagingSenderId: "455276978813",
  appId:        "1:455276978813:web:…"
};

// initialize
const app = initializeApp(firebaseConfig);
export const db  = getFirestore(app);