# Use Python 3.11 as the base image
FROM python:3.11

# Set working directory
WORKDIR /app

# Copy requirements.txt into the container
COPY requirements.txt /app/

# Upgrade pip
RUN pip install --upgrade pip

# Install project dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files into the container
COPY . /app/

# Expose port 5000
EXPOSE 5000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Run the application
CMD ["gunicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"]