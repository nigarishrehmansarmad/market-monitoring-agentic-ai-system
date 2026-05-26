FROM python:3.11-slim

WORKDIR /app

# gcc/g++ needed by sentence-transformers and numpy C extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p charts

EXPOSE 7860

CMD ["streamlit", "run", "dashboard.py", \
     "--server.address=0.0.0.0", \
     "--server.port=7860", \
     "--server.headless=true"]
