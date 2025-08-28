FROM python:3.11-slim
RUN apt-get update && apt-get install -y curl git && rm -rf /var/lib/apt/lists/*
RUN curl -fsSL https://raw.githubusercontent.com/google-gemini/gemini-cli/main/install.sh | bash
ENV PATH="/root/.local/bin:$PATH"
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "main.py"]
