/**
 * firebase-init.js
 *
 * Initializes the Firebase client SDK (used by the browser for
 * Authentication + direct Firestore reads where appropriate).
 *
 * Loaded via the Firebase "compat" SDK script tags (see any page's
 * <head>) so it works with plain <script> tags -- no build step needed.
 * `firebase.auth()` and `firebase.firestore()` become available globally
 * after this file runs.
 */

const firebaseConfig = {
  apiKey: "AIzaSyAMOddGHg88MvvMrJfa13-rgx7RwWTOAGU",
  authDomain: "smart-inventory-system-6dea3.firebaseapp.com",
  projectId: "smart-inventory-system-6dea3",
  storageBucket: "smart-inventory-system-6dea3.firebasestorage.app",
  messagingSenderId: "690460704479",
  appId: "1:690460704479:web:eedc774e4cd350d03f736a",
};

firebase.initializeApp(firebaseConfig);

// Shared handles used across all page scripts (login.js, signup.js, etc.)
window.firebaseAuth = firebase.auth();
window.firestoreDb = firebase.firestore();
