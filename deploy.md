# Deploying ShikshaSetu 🚀

This guide provides step-by-step instructions to deploy the **ShikshaSetu** application in a production environment:
* **Backend**: FastAPI deployed to **Render**
* **Frontend**: React + TypeScript + Vite deployed to **Vercel**
* **Database**: MongoDB Atlas

---

## 📋 Prerequisites & Preparation

1. **MongoDB Atlas Cluster**:
   * Create a free M0 cluster on MongoDB Atlas.
   * Go to **Database Access** and create a user with read/write privileges.
   * Go to **Network Access** and add `0.0.0.0/0` (allow access from anywhere) so Render can connect.
   * Copy the Connection String (e.g., `mongodb+srv://<username>:<password>@cluster0.xxxx.mongodb.net/?retryWrites=true&w=majority`).

2. **Google Gemini API Key**:
   * Get an API key from Google AI Studio.

3. **Git Repository**:
   * Ensure all code modifications (including lockfiles) are pushed to your GitHub repository:
     ```bash
     git add -A
     git commit -m "prep: deployment configuration updates"
     git push origin main
     ```

---

## 🐍 Part 1: Deploy Backend on Render

Render is ideal for hosting Python services like FastAPI.

### Step 1: Create a Web Service
1. Sign in to your [Render Dashboard](https://dashboard.render.com).
2. Click **New +** and select **Web Service**.
3. Connect your GitHub repository.

### Step 2: Configure Settings
* **Name**: `shikshasetu-backend` (or a name of your choice)
* **Region**: Choose a region close to your target users (e.g., `Singapore` or `Oregon`)
* **Branch**: `main`
* **Root Directory**: `backend` (⚠️ *Very Important: points to the backend folder*)
* **Runtime**: `Python`

### Step 3: Build & Start Commands
* **Build Command**: 
  ```bash
  pip install -r requirements.txt
  ```
* **Start Command**: 
  ```bash
  uvicorn app.main:app --host 0.0.0.0 --port $PORT
  ```

### Step 4: Configure Environment Variables
Click **Advanced** and add the following keys under **Environment Variables**:

| Key | Value | Notes |
|---|---|---|
| `MONGODB_URI` | `mongodb+srv://...` | Your MongoDB Atlas connection string |
| `JWT_SECRET` | `generate-a-long-random-string-here` | Secret key for generating auth tokens |
| `GEMINI_API_KEY` | `your-gemini-api-key` | Google GenAI credentials |
| `ENVIRONMENT` | `production` | Enables production mode |

### Step 5: Save & Deploy
* Click **Create Web Service** at the bottom of the page.
* Render will clone your repo, install the dependencies (including `python-multipart`), and bind to the correct port.
* Once the build completes, copy the service URL (e.g., `https://shikshasetu-m8xv.onrender.com`).

---

## ⚡ Part 2: Deploy Frontend on Vercel

Vercel is optimized for building and serving static frontend assets.

### Step 1: Create a Project
1. Log in to your [Vercel Dashboard](https://vercel.com/dashboard).
2. Click **Add New** and select **Project**.
3. Import your GitHub repository.

### Step 2: Configure Project Settings
* **Framework Preset**: `Vite` (Vercel should detect this automatically)
* **Root Directory**: `frontend` (⚠️ *Very Important: click Edit and select the `frontend` folder*)

### Step 3: Build and Output Settings
Under **Build and Output Settings**, toggle and modify:
* **Build Command**: 
  ```bash
  pnpm run build
  ```
  *(or `npm run build` if you prefer npm)*
* **Output Directory**: 
  ```text
  dist/public
  ```
  *(⚠️ Note: Vite is configured to build to `dist/public` in this repository's `vite.config.ts`)*
* **Install Command**:
  ```bash
  pnpm install
  ```
  *(or `npm install`)*

### Step 4: Environment Variables
Add the following variable to connect the frontend to your Render API:

| Name | Value | Notes |
|---|---|---|
| `VITE_API_URL` | `https://your-backend-url.onrender.com/api/v1` | Replace with your live Render backend URL |

### Step 5: Deploy
* Click **Deploy**.
* Vercel will build the React bundles and serve them on a fast CDN.
* If you run into navigation route issues on refresh, add a `vercel.json` file in the `frontend` directory containing:
  ```json
  {
    "rewrites": [{ "source": "/(.*)", "destination": "/" }]
  }
  ```

---

## 🧪 Part 3: Verify Deployment

Once both deployments are successful:
1. Navigate to your Vercel frontend URL.
2. Sign up / login using the standard portal options.
3. Inspect network requests using Developer Tools (F12) to verify it is communicating with your secure Render endpoint (`/api/v1`).
4. Ensure all pages (Dashboard, Competencies, Gaps, Quizzes, Recommendations) function correctly without any mock status.
