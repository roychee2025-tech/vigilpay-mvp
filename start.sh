#!/data/data/com.termux/files/usr/bin/bash

cd ~/vigilpay

source .venv/bin/activate

echo "Starting VigilPay..."
echo "Open: http://127.0.0.1:8000/demo"

uvicorn app:app --host 0.0.0.0 --port 8000
