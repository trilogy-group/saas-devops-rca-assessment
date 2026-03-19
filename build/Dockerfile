FROM python:3.11-slim

RUN pip install --no-cache-dir pyinstaller

WORKDIR /build
COPY src/submit.py .

RUN pyinstaller \
    --onefile \
    --name submit \
    --strip \
    --clean \
    submit.py

# Output binary is at /build/dist/submit
