# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV CUSTOM_API_KEY=123

# Set the working directory
WORKDIR /app

# Copy the source code into the container
COPY . .

# Build the Python project
RUN pip install build
RUN python -m build

# Install the package from the build output
RUN pip install dist/*.whl

# Expose port 8000 for the server
EXPOSE 8000

# Set the entrypoint for the container
ENTRYPOINT ["moderator"]

# Default command to start the server
CMD ["start-server", "--host", "0.0.0.0", "--port", "8000"]
