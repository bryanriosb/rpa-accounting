FROM mcr.microsoft.com/playwright:v1.54.0-noble

# Set the working directory
WORKDIR /app

# Install pip
RUN apt-get update && apt-get install -y python3-pip

# Copy the requirements file and install dependencies
COPY requirements.txt /app/
RUN pip3 install --no-cache-dir -r requirements.txt --break-system-packages

# Copy the Python application code
COPY credit-notes/python/ /app/

# Create directories for volumes
RUN mkdir -p /app/notes_downloads /app/logs

# Set the command to run the application
CMD ["python3", "main.py"]