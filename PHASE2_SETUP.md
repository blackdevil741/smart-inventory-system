# Local Setup Guide — Phase 2

This project is now wired to a real Firebase project:
**`smart-inventory-system-6dea3`**

Follow these steps on your own computer to run it.

---

## 1. Backend setup

```bash
cd backend
python -m venv venv

# Activate the virtual environment:
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows

pip install -r requirements.txt
```

### Add your service account key

You should already have downloaded a file named something like
`smart-inventory-system-6dea3-firebase-adminsdk-fbsvc-....json` from the
Firebase Console.

1. Rename it to exactly: `firebase-service-account.json`
2. Place it directly inside the `backend/` folder (next to `app.py`)

**Never commit this file to GitHub.** It's already listed in `.gitignore`,
so `git add .` won't pick it up — but double-check before pushing.

### Create your `.env` file

```bash
cp .env.example .env
```

Then open `.env` and make sure it looks like this:

```
FLASK_ENV=development
FLASK_DEBUG=1
SECRET_KEY=dev-secret-key-change-in-production
PORT=5000

ALLOWED_ORIGINS=http://localhost:5500,http://127.0.0.1:5500

FIREBASE_SERVICE_ACCOUNT_PATH=./firebase-service-account.json
FIREBASE_PROJECT_ID=smart-inventory-system-6dea3
FIREBASE_STORAGE_BUCKET=
```

(`FIREBASE_STORAGE_BUCKET` is intentionally left blank — this project
does not use Firebase Storage, to keep everything on the free Spark plan.)

### Run it

```bash
python app.py
```

You should see Flask start on `http://localhost:5000`. Visit
`http://localhost:5000/api/health` in your browser — you should see:

```json
{"success": true, "data": {"status": "ok", "service": "Smart Inventory System API", "firebase": "connected"}}
```

If `firebase` says anything other than `"connected"`, double check the
service account file is in the right place and named exactly right.

---

## 2. Frontend setup

No build step needed — plain HTML/CSS/JS.

```bash
cd frontend
python -m http.server 5500
```

Then open: **http://localhost:5500/pages/login.html**

Try creating an account on the **Sign up** page. If everything's wired
correctly:
1. It creates a real Firebase Auth account
2. It creates a matching profile document in Firestore (`users/{uid}`)
3. You're redirected to a placeholder dashboard confirming you're logged in

You can check the Firestore data landed correctly here:
```
https://console.firebase.google.com/project/smart-inventory-system-6dea3/firestore/data
```
You should see a `users` collection with a document containing your
shop name, email, and role.

---

## 3. Apply real Firestore security rules

Right now your database is in **test mode**, which means anyone with your
project ID could read/write it. Let's lock it down properly.

1. Go to:
   ```
   https://console.firebase.google.com/project/smart-inventory-system-6dea3/firestore/rules
   ```
2. Delete everything in the editor
3. Open `firebase/firestore.rules` from this project and paste its
   entire contents in
4. Click **Publish**

This restricts data access to signed-in users only, and ensures each
user can only read/write their own profile document.

---

## Troubleshooting

**"Firebase service account key not found"**
→ Check the file is named exactly `firebase-service-account.json` and
sits directly inside `backend/`, not in a subfolder.

**CORS errors in the browser console**
→ Make sure the frontend is running on `http://localhost:5500` (or update
`ALLOWED_ORIGINS` in `.env` to match whatever port you're actually using).

**"Missing or malformed Authorization header"**
→ This means a frontend page tried to call a protected backend route
without a valid Firebase ID token. Make sure you're logged in.

**Signup succeeds in Firebase Auth but shows a profile error**
→ This means the Auth account was created but the backend call to
`/api/auth/register-profile` failed — check that `python app.py` is
running and reachable at `http://localhost:5000`.
