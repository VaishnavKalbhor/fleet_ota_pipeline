FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# --host 0.0.0.0 is required here -- uvicorn defaults to binding 127.0.0.1,
# which inside a container is only reachable from within that container's
# own network namespace. Without this flag `docker run -p 8000:8000 ...`
# starts successfully and looks fine, but the host can never connect.
# See docs/mistakes-log.md.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
