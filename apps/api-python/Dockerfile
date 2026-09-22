# ── Prospex Lead Generation — Railway Deployment ────────────────────────────
# Single container: Python backend + pre-built React frontend + Playwright

FROM python:3.11-slim

# System dependencies for Playwright + general
RUN apt-get update && apt-get install -y \
    wget curl gnupg ca-certificates \
    libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 \
    libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 \
    libgbm1 libasound2 libpango-1.0-0 libcairo2 \
    fonts-liberation libappindicator3-1 libu2f-udev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN python -m playwright install chromium --with-deps 2>/dev/null || \
    python -m playwright install chromium

# Copy application code
COPY . .

# Demo mode is ON by default for Railway deployment
RUN echo '{"demo_mode": true, "demo_buy_link": "https://wa.me/923001234567?text=I+want+to+buy+Prospex", "demo_contact_name": "Zohai Agency", "demo_price": ""}' > /app/demo_config.json

# Set environment
ENV ENV=production
ENV PORT=8000
ENV DATABASE_URL=sqlite+aiosqlite:///./prospex_demo.db

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
