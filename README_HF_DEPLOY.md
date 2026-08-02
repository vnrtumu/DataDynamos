# Deploying Backend to Hugging Face Spaces (100% Free Docker Hosting)

Hugging Face Spaces provides **16 GB RAM and 2 vCPUs completely free**, supporting custom Docker containers natively.

---

## Step 1: Create your Space on Hugging Face

1. Log in to [Hugging Face](https://huggingface.co/) (create a free account if you don't have one).
2. Go to [https://huggingface.co/new-space](https://huggingface.co/new-space).
3. Fill in space details:
   - **Owner**: Select your username or organization.
   - **Space Name**: e.g., `datadynamos-backend`
   - **License**: `MIT` or leave default.
   - **Select the Space SDK**: Choose **Docker**.
   - **Choose a Docker template**: Select **Blank**.
   - **Space Hardware**: Keep **CPU Basic (2 vCPU, 16 GB RAM) - Free**.
   - **Visibility**: **Public** (or Private if desired).
4. Click **Create Space**.

---

## Step 2: Configure Environment Secrets

1. Go to your newly created Space settings: `https://huggingface.co/spaces/<YOUR_USERNAME>/datadynamos-backend/settings`.
2. Scroll to **Variables and secrets**.
3. Click **New secret**:
   - **Key**: `OPENROUTER_API_KEY`
   - **Value**: `sk-or-v1-...` (your OpenRouter API key from `backend/.env`)
4. (Optional) Add **New variable**:
   - **Key**: `OCR_DEFAULT_ENGINE`
   - **Value**: `qwen-vl`

---

## Step 3: Push Code to your Space

You can push your repository to Hugging Face via Git:

```bash
# Add Hugging Face Git remote (replace <YOUR_USERNAME> with your HF username)
git remote add hf https://huggingface.co/spaces/<YOUR_USERNAME>/datadynamos-backend

# Push your code to build the container
git push hf main
```

*Note: If prompted for password when pushing to Hugging Face via Git, generate an Access Token at [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) with `write` permission and use it as your password.*

---

## Step 4: Verify Deployment

Once Hugging Face completes building the Docker container (takes ~2-3 minutes):

1. **Live Health Check Endpoint**:
   ```bash
   curl https://<YOUR_USERNAME>-datadynamos-backend.hf.space/health
   ```
   *Expected response*: `{"status":"ok"}`

2. **Interactive API Documentation (Swagger)**:
   Open `https://<YOUR_USERNAME>-datadynamos-backend.hf.space/docs` in your browser.
