FROM python:3.12-alpine

WORKDIR /app
COPY exporter.py .

EXPOSE 9100
CMD ["python", "-u", "exporter.py"]
