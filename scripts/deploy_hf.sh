#!/usr/bin/env bash
set -e

# DataDynamos Hugging Face Spaces Deployment Script

HF_USERNAME=$1
SPACE_NAME=${2:-datadynamos-backend}

if [ -z "$HF_USERNAME" ]; then
    echo "Usage: ./scripts/deploy_hf.sh <hf_username> [space_name]"
    echo "Example: ./scripts/deploy_hf.sh myusername datadynamos-backend"
    exit 1
fi

REMOTE_URL="https://huggingface.co/spaces/${HF_USERNAME}/${SPACE_NAME}"

echo "==> Configuring Git Remote for Hugging Face Space: ${REMOTE_URL}"

if git remote get-url hf >/dev/null 2>&1; then
    git remote set-url hf "${REMOTE_URL}"
else
    git remote add hf "${REMOTE_URL}"
fi

echo "==> Pushing repository main branch to Hugging Face Spaces..."
git push hf main

echo "==> Deployment trigger complete!"
echo "Check build logs and live app status at: https://huggingface.co/spaces/${HF_USERNAME}/${SPACE_NAME}"
echo "Live Health Check URL: https://${HF_USERNAME}-${SPACE_NAME}.hf.space/health"
