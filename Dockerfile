# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# Using --no-cache-dir to reduce image size
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container at /app
# This includes main.py and the mcp_server directory, and static files
COPY . .

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Define environment variable for the application port if needed by uvicorn
# ENV PORT 8000 # Uvicorn default is 8000, so not strictly necessary unless changing

# Run main.py when the container launches
# Use 0.0.0.0 to bind to all interfaces, making it accessible from outside the container
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
