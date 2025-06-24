FROM python:3.10

# Set working directory to /app
WORKDIR /app

# Copy everything into container
COPY . .

# Change working directory to where main.py lives
WORKDIR /app/Server

# Install dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

# Expose port
EXPOSE 8000

# Set start command (entry point)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
