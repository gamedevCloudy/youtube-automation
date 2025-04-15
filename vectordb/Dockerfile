FROM python:3.10-slim

WORKDIR /app

# Install Poetry
RUN pip install poetry

# Copy poetry configuration files
COPY pyproject.toml poetry.lock* /app/

# Configure poetry to not create a virtual environment
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry install --no-dev

# Copy the application code
COPY src/ /app/src/

# Create data directory for ChromaDB
RUN mkdir -p /app/data

# Run the application
CMD ["python", "-m", "vectordb.main"]