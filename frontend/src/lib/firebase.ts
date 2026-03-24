import { FirebaseApp, getApp, getApps, initializeApp } from "firebase/app";
import { Auth, getAuth } from "firebase/auth";
import { Firestore, getFirestore } from "firebase/firestore";

const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID,
};

let firebaseApp: FirebaseApp | null = null;
let firebaseAuth: Auth | null = null;
let firebaseDb: Firestore | null = null;

function hasRequiredConfig() {
  return (
      !!firebaseConfig.apiKey &&
      !!firebaseConfig.authDomain &&
      !!firebaseConfig.projectId &&
      !!firebaseConfig.appId
  );
}

function getFirebaseApp(): FirebaseApp | null {
  if (typeof window === "undefined") return null;
  if (!hasRequiredConfig()) return null;

  if (firebaseApp) return firebaseApp;

  firebaseApp = getApps().length ? getApp() : initializeApp(firebaseConfig);
  return firebaseApp;
}

export function getFirebaseAuth(): Auth | null {
  if (firebaseAuth) return firebaseAuth;

  const app = getFirebaseApp();
  if (!app) return null;

  firebaseAuth = getAuth(app);
  return firebaseAuth;
}

export function getFirebaseDb(): Firestore | null {
  if (firebaseDb) return firebaseDb;

  const app = getFirebaseApp();
  if (!app) return null;

  firebaseDb = getFirestore(app);
  return firebaseDb;
}
