# Deploying Backend to Koyeb (100% Free Always-On Docker Hosting)

[Koyeb](https://koyeb.com) provides a **100% Free Eco Tier** that supports custom Docker containers and **does not sleep after inactivity**.

---

## Step 1: Sign up on Koyeb
1. Go to [koyeb.com](https://app.koyeb.com/auth/signup) and create a free account (Sign in with GitHub).

## Step 2: Create a New App
1. Click **Create Service** in the Koyeb dashboard.
2. Select **GitHub** as the deployment method.
3. Choose your repository: `tvnrr690/DataDynamos` (or your repo name).
4. Branch: Select `feature/Venky-Huggingface` (or `main`).

## Step 3: Configure Builder & Environment Settings
1. Under **Builder**, select **Dockerfile** (it will auto-detect `/Dockerfile`).
2. Under **Ports**, set internal port to `8000` (HTTP).
3. Under **Environment Variables**, click **Add Variable**:
   - `OPENROUTER_API_KEY`: `sk-or-v1-...` (your key from `backend/.env`)
   - `OCR_DEFAULT_ENGINE`: `qwen-vl` (or `mock`)
4. Instance Type: Select **Eco Nano** (Free).

## Step 4: Deploy & Access App
1. Click **Deploy**.
2. Koyeb will build the Docker container and assign a live HTTPS URL (e.g., `https://datadynamos-backend-<username>.koyeb.app`).
3. Check status:
   - Health Check: `https://<your-app-name>.koyeb.app/health`
   - API Docs: `https://<your-app-name>.koyeb.app/docs`
