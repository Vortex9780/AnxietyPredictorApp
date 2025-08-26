// firebaseConfig.ts
import { initializeApp } from 'firebase/app';
import { getAuth }       from 'firebase/auth';
import { getFirestore }  from 'firebase/firestore';

// ← replace the values below with your actual Firebase console values
const firebaseConfig = {
   apiKey: "AIzaSyBKBEN7PJDhbLLMgqQb8Tz_DzKTIlwqaFY",
  authDomain: "anxietypredictor-43c43.firebaseapp.com",
  projectId: "anxietypredictor-43c43",
  storageBucket: "anxietypredictor-43c43.firebasestorage.app",
  messagingSenderId: "455276978813",
  appId: "1:455276978813:web:20585dfc0beadb3d1e4714"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Export the services you need
export const auth = getAuth(app);
export const db   = getFirestore(app);