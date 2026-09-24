FROM python:3.11-slim

# System dependencies for Playwright
RUN apt-get update && apt-get install -y \
    wget curl gnupg ca-certificates gcc \
    libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 \
    libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 \
    libgbm1 libasound2 libpango-1.0-0 libcairo2 libx11-6 libx11-xcb1 \
    libxcb1 libxext6 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy EVERYTHING from the repo root
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r apps/api-python/requirements.txt

# Install Playwright chromium
RUN python -m playwright install chromium --with-deps || python -m playwright install chromium

# Set working dir to the api-python app
WORKDIR /app/apps/api-python

# Write demo config
RUN echo '{"demo_mode": true, "demo_buy_link": "https://wa.me/923001234567?text=I+want+to+buy+Prospex", "demo_contact_name": "Zohai Agency", "demo_price": ""}' > demo_config.json

ENV ENV=production
ENV DATABASE_URL=sqlite+aiosqlite:///./prospex_demo.db

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
