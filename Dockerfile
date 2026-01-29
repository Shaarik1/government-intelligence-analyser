# 1. Use Python 3.11 (Stable Gold Standard)
# This solves all the dependency hell you had with Python 3.14
FROM python:3.11-slim

# 2. Set the working folder inside the container
WORKDIR /app

# 3. Copy requirements and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy your application code
COPY . .

# 5. Expose the port
EXPOSE 8000

# 6. Run the app
# We bind to 0.0.0.0 so the container is accessible from outside
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]