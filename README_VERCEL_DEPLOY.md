# Deploying Frontend to Vercel

The **DataDynamos React + Vite Frontend** is fully prepared for instant 1-click deployment on [Vercel](https://vercel.com).

---

## ⚡ 5-Step Guide to Deploy on Vercel

### Step 1: Log in to Vercel
1. Go to [vercel.com/new](https://vercel.com/new) and sign in with your GitHub account (`vnrtumu`).

### Step 2: Import Project
1. Select your repository: `vnrtumu/DataDynamos`.
2. Select branch: `feature/Venky-Huggingface` (or `main`).

### Step 3: Configure Build & Framework Settings
Vercel automatically detects Vite:
- **Framework Preset**: `Vite`
- **Root Directory**: `./`
- **Build Command**: `pnpm build` (or `npm run build`)
- **Output Directory**: `dist`

### Step 4: Set Environment Variable for Backend API
Expand **Environment Variables** and add:
- **Key**: `VITE_API_BASE_URL`
- **Value**: `https://datadynamos.onrender.com`

*(This points your Vercel frontend directly to your live backend on Render!)*

### Step 5: Deploy
1. Click **Deploy**.
2. Vercel will build and publish your frontend in ~30 seconds with a free HTTPS domain (e.g. `https://datadynamos.vercel.app`).
