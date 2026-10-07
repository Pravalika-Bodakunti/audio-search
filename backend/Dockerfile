FROM python:3.11-slim
# small Python base image
WORKDIR /app
# all commands run inside /app
COPY requirements.txt .
# copy deps first so Docker caches this layer
RUN pip install --no-cache-dir -r requirements.txt
# install the Python packages
COPY . .
# copy the app code
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
# start the API, reachable from outside the container
