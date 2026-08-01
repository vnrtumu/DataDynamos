# Deploying Backend to Render (100% Free Docker Web Service)

[Render](https://render.com) provides a **100% Free Web Service** tier that natively supports custom Dockerfiles.

---

## Step 1: Sign up / Log in to Render
1. Go to [dashboard.render.com](https://dashboard.render.com/) and sign in with GitHub (`Venkat Reddy` / `vnrtumu`).

---

## Step 2: Create a New Web Service
1. In the top right of the Render dashboard, click **New +** -> select **Web Service**.
2. Choose **Build and deploy from a Git repository** -> click **Next**.
3. Connect your GitHub repository (`vnrtumu/DataDynamos` or `DataDynamos`).

---

## Step 3: Configure Web Service Settings
Fill in the following fields:
- **Name**: `datadynamos-backend`
- **Region**: Select your closest region (e.g. Singapore, Oregon, Frankfurt)
- **Branch**: `feature/Venky-Huggingface` (or `main`)
- **Root Directory**: Leave blank (uses project root)
- **Language / Runtime**: Select **Docker**
- **Instance Type**: Select **Free ($0/mo)**

---

## Step 4: Add Environment Variables
Scroll down to **Environment Variables** (or **Advanced**) and click **Add Environment Variable**:
1. `OPENROUTER_API_KEY` = `<your OpenRouter key from backend/.env>`
2. `OCR_DEFAULT_ENGINE` = `qwen-vl`

---

## Step 5: Deploy & Access App
1. Click **Create Web Service**.
2. Render will build your Docker image (`python:3.12-slim` + `tesseract-ocr` + `uv`) and give you a live URL:
   `https://datadynamos-backend.onrender.com`
3. Test status:
   - **Health Check**: `https://datadynamos-backend.onrender.com/health`
   - **Interactive Docs**: `https://datadynamos-backend.onrender.com/docs`
