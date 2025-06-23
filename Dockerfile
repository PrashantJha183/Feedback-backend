FROM python:3.10

# Set working directory to /app/Server
WORKDIR /app

COPY . .

WORKDIR /app/Server  # <== this is the key fix

# Install dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

# Expose port
EXPOSE 8000

# Run your app (main.py inside app/)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
