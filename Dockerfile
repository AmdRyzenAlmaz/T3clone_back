FROM python:3.13

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN pip install uv

WORKDIR /app

# Copy dependency files first to leverage Docker cache
COPY uv.lock .
COPY pyproject.toml .

# Install dependencies using uv
RUN uv pip install --system .

# Copy the rest of the application
COPY . .

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["fastapi", "run", "src/main.py", "--host", "0.0.0.0", "--port", "8000"]

