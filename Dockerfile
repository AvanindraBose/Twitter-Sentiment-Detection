FROM python:3.11

# Create a workdir
WORKDIR /app/

# COPY pyproject.toml and uv.lock files
COPY pyproject.toml uv.lock ./
# Copy scripts to download nltk library
COPY ./scripts scripts/
# Copy the contents of our workdir
COPY ./backend/ backend/
# Copying Src Directory
COPY ./src src/

# Install pip
RUN pip install uv
RUN uv sync --frozen

# RUN to install nltk library
RUN uv run python scripts/setup_nltk.py

# Port
EXPOSE 5000

# Command -> Executed when a container is build on top of it
CMD ["uv","run","uvicorn","backend.main:app","--host","0.0.0.0","--port","5000"]

