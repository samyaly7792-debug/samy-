FROM python:3.11-slim

WORKDIR /app

# Copy project files
COPY . /app

# Upgrade pip/setuptools/wheel inside the image and install requirements
RUN python -m pip install --upgrade pip setuptools wheel
RUN pip install -r requirements.txt

# Ensure uploads folder exists and is writable
RUN mkdir -p /app/uploads

# Expose a port (Render will set PORT at runtime). Provide a sensible default.
EXPOSE 8000
ENV PORT=8000

# Start the app using gunicorn + eventlet and bind to $PORT provided by the platform
CMD ["sh", "-c", "gunicorn -k eventlet -w 1 -b 0.0.0.0:${PORT} app:app --log-file -"]
