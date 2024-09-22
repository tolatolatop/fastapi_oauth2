FROM python:3.10.2-slim

# Set the working directory
WORKDIR /app

COPY requirements.txt /app
# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY *.py /app/app.py

# Make port 80 available to the world outside this container
EXPOSE 80

# COMMAND to uvicorn app:app --reload
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "80"]
