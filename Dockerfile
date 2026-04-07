# Use a Conda-based image (Mamba is a faster alternative for scientific libraries)
FROM mambaforge/mambaforge:latest

WORKDIR /app

# 1. Create a conda environment and install dependencies
# Note: CadQuery and OCP are best installed via mamba to handle shared libraries correctly
RUN mamba install -y -c cadquery -c conda-forge \
    python=3.9 \
    cadquery=2.4.0 \
    pytorch \
    shapely \
    fastapi \
    uvicorn \
    python-multipart \
    scikit-learn \
    joblib \
    pillow \
    matplotlib \
    && mamba clean -afy

# 2. Copy the entire core backend application
# (Repository weights, iGenerator, ModelGeneratorCQ)
COPY . /app

# 3. Expose the port used by Render (Render looks for PORT env variable, defaulting to 10000)
# We set 8000 for standard FastAPI local dev match
EXPOSE 8000

# 4. Start the FastAPI server
# We use --host 0.0.0.0 so Render can route traffic to the container
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
