FROM python:3.7-slim-stretch

# Copy only the relevant Python files into the container.
COPY . /svc

# Set the work directory to the app folder.
WORKDIR /svc

# Install Python dependencies.
RUN pip3 install -r requirements.txt

ENTRYPOINT ["python3", "main.py"]
