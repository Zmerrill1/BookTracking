# Use the official Python image as a base
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    UV_NO_INDEX=1

# Set the working directory inside the container
WORKDIR /app

# Copy only the necessary files first for better caching
COPY pyproject.toml uv.lock ./

# Install uv and project dependencies
RUN pip install uv && uv venv && .venv/bin/uv pip install --system

# Copy the rest of the application code
COPY . .

# Expose the FastAPI default port
EXPOSE 8000

# Run the application
CMD ["uv", "run", "python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
