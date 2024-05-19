# Use an official Python runtime as a parent image
FROM python:3.9-slim

RUN apt-get update && apt-get install -y git && apt-get clean

# Set the working directory in the container
WORKDIR /app

# Copy requirements file and install dependencies
#RUN echo "numpy" >> requirements.txt
#RUN echo "github" >> requirements.txt

COPY requirements /app/requirements

COPY requirements /app/requirements.txt

#RUN pip freeze > requirements.txt
RUN pip install -r /app/requirements

# Copy the rest of the application
COPY CS401_GithubAnalyzer /app/CS401_GithubAnalyzer

WORKDIR /app/CS401_GithubAnalyzer/PY

# Run ui.py when the container launches
CMD ["python", "ui.py"]
