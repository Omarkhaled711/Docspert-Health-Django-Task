# Step 1: Use an official Python runtime as a parent image
FROM python:latest

# Step 2: Set environment variables
ENV PYTHONUNBUFFERED=1

# Step 3: Set the working directory in the container
WORKDIR /app

# Step 4: Copy the current directory contents into the container at /app
COPY . /app/

# Step 5: Install dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt


# step 6: change directory to account_transfer
WORKDIR /app/account_transfer

# step 7: Make Migrations
RUN python manage.py makemigrations
RUN python manage.py migrate

# Step 8: Expose port 8000 (Django default)
EXPOSE 8000

# Step 9: Run the Django development server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
