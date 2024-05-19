# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy requirements file and install dependencies
RUN echo "numpy" >> requirements.txt
COPY requirements /app/requirements
RUN pip freeze > requirements.txt

# Copy the rest of the application
COPY ui.py /app

# Run ui.py when the container launches
CMD ["python", "ui.py"]
