FROM python:3.11-slim

# System dependencies for Playwright
RUN apt-get update && apt-get install -y \
    wget curl gnupg ca-certificates gcc \
    libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 \
    libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 \
    libgbm1 libasound2 libpango-1.0-0 libcairo2 libx11-6 libx11-xcb1 \
    libxcb1 libxext6 && rm -rf /var/lib/apt/lists/*

# Set working directory to the api-python app
WORKDIR /app/apps/api-python

# Install Python dependencies
COPY apps/api-python/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright chromium
RUN python -m playwright install chromium --with-deps || python -m playwright install chromium

# Copy the entire project
COPY apps/api-python/ .

# Copy built frontend static files
COPY apps/api-python/static/ ./static/

# Set demo mode ON
RUN echo '{"demo_mode": true, "demo_buy_link": "https://wa.me/923001234567?text=I+want+to+buy+Prospex", "demo_contact_name": "Zohai Agency", "demo_price": ""}' > /app/apps/api-python/demo_config.json

ENV ENV=production
ENV DATABASE_URL=sqlite+aiosqlite:///./prospex_demo.db
ENV JWT_SECRET=prospex_demo_jwt_secret_2024
ENV ENCRYPTION_KEY=prospex32charencryptionkey123456

EXPOSE $PORT

CMD python -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
