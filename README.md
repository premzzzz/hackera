Here's an updated README with instructions for setting up Ollama with Llama 3.1 on your local machine:

---

# Team Monday
- **Kartikey Sapkal**
- **Nachiket Kulkarni**

# Online Debate App

### Always check for the updated branch or use the default branch

## Overview

Debate App is a web application built using Flask that allows users to engage in debates with an AI. Users can register, log in, start debates, and view their performance metrics over time. The application also supports saving and visualizing debate scores using Plotly.

## Features

- **User Registration and Authentication**: Users can sign up, log in, and manage their accounts.
- **Debate System**: Engage in debates with AI, track debate history, and receive AI responses.
- **Visualization**: Plotly-based visualization of debate scores.
- **Database Integration**: PostgreSQL database for storing user data and debate scores.

## Technologies Used

- **Flask**: Web framework for building the application.
- **Langchain**: Library for natural language processing.
- **Plotly**: Library for creating interactive graphs.
- **PostgreSQL**: Relational database for data storage.
- **Docker**: Containerization platform to run the application in isolated environments.
- **Trivi**: Vulnerability scanning for docker containers.
- **HTML/CSS/JS**: Providing overall user experience.

## Screenshots

### User Interface

| ![Home Page](images/home_page.jpeg) | ![Register Page](images/register_page.jpeg) |
|:----------------------------------:|:------------------------------------------:|
| Home Page                           | Register Page                              |

### Debate Experience

| ![SingleUser](images/single_user_1_2.jpeg) | ![Multiuser](images/multi_user.jpeg) |
|:--------------------------------------:|:---------------------------------:|
| AI vs User Page                            | Multi-User Page                           |

| ![Dashboard](images/dashboard_page.jpeg) | 
|:--------------------------------------:|
| Dashboard                              |

## Setup Instructions

### Prerequisites

- Python 3.x
- PostgreSQL
- Docker (for containerized setup)
- Ollama with Llama 3.1 (for AI debates)

### Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/yourusername/debate-app.git
   cd debate-app
   ```

2. **Set Up Environment Variables**

   Create a `.env` file in the root directory with the following environment variables:

   ```env
   SECRET_KEY=your_secret_key
   DB_USER=your_db_user
   DB_HOST=your_db_host
   DB_NAME=your_db_name
   DB_PASSWORD=your_db_password
   DB_PORT=your_db_port
   ```

3. **Install Dependencies**

   It is recommended to use a virtual environment. Install the required Python packages:

   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize the Database**

   Run the application to initialize the database:

   ```bash
   python app.py
   ```

   This will create the necessary tables and columns in your PostgreSQL database.

5. **Run the Application**

   Start the Flask development server:

   ```bash
   python app.py
   ```

   The application will be available at `http://127.0.0.1:5000`.

### Ollama Setup with Llama 3.1 on Local Machine

1. **Install Ollama**

   Download and install Ollama on your local machine from [Ollama's official website](https://ollama.com).

2. **Download the Llama 3.1 Model**

   After installing Ollama, download the Llama 3.1 model by running:

   ```bash
   ollama pull llama3.1
   ```

3. **Start Ollama Service**

   Run the Ollama service on your local machine:

   ```bash
   ollama serve --model llama3.1
   ```

   This will start the Ollama service and make it accessible on `http://localhost:11434`.

4. **Configure Flask App to Use Ollama**

   Ensure your Flask application is configured to interact with the Ollama service running on your local machine. Update the `.env` file with the following variable if required:

   ```env
   OLLAMA_ENDPOINT=http://localhost:11434
   ```

### Docker Setup

If you prefer to run the application using Docker, follow these steps:

1. **Create a Dockerfile**

   Your `Dockerfile` should look like this:

   ```Dockerfile
   # Use Python 3.9 slim image
   FROM python:3.9-slim

   # Set the working directory
   WORKDIR /app

   # Copy requirements and install Python dependencies
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt --verbose

   # Copy application code
   COPY static /app/static/
   COPY templates /app/templates/
   COPY app.py /app/

   # Create upload directory
   RUN mkdir -p /app/uploads

   # Copy environment variables
   COPY .env /app/.env

   # Expose port
   EXPOSE 5000

   # Command to run the Flask app
   CMD ["python", "app.py"]
   ```

2. **Create a Docker Compose File**

   Your `docker-compose.yml` file should look like this:

   ```yaml
   version: "3.8"

   services:
     web:
       build:
         context: .
         dockerfile: Dockerfile
       ports:
         - "5000:5000"
       volumes:
         - .:/app
       environment:
         - DB_USER=docker
         - DB_PASSWORD=docker
         - DB_NAME=docker
         - DB_HOST=docker
         - DB_PORT=5432
         - SECRET_KEY=your_secret_key # Set your secret key
       networks:
         - app-network
       depends_on:
         - ollama-service
         - postgres

     ollama-service:
       image: ollama/ollama:latest
       container_name: ollama-service
       ports:
         - "11434:11434"
       volumes:
         - ollama:/root/.ollama
       networks:
         - app-network

     postgres:
       image: postgres:13
       container_name: postgres
       environment:
         POSTGRES_USER: docker
         POSTGRES_PASSWORD: docker
         POSTGRES_DB: docker
       ports:
         - "5432:5432"
       networks:
         - app-network

   networks:
     app-network:
       driver: bridge

   volumes:
     ollama:
       driver: local
   ```

3. **Build and Run the Docker Containers**

   - Build the Docker image and start the containers:

     ```bash
     docker-compose up --build
     ```

   - The application will be available at `http://localhost:5000`.

## Troubleshooting

- **Database Connection Issues**: Ensure that your PostgreSQL database is running and the environment variables are correctly set in both `.env` and `docker-compose.yml`.
- **File Not Found Errors**: Verify that the file paths and names in the `Dockerfile` and application code are correct.
- **Dependencies Installation**: If you encounter issues with package installation, ensure all build dependencies are installed. For Alpine-based images, you may need to add `build-base`, `swig`, and `cmake` (commented out in the Dockerfile).

## Usage

1. **Access the Application**

   Navigate to `http://127.0.0.1:5000` in your web browser.

2. **Register and Log In**

   Use the `/register` endpoint to create a new account and `/login` to authenticate.

3. **Start a Debate**

   Go to `/single_user` to start a new debate. You can then use `/debate` to interact with the AI and `/end_debate` to finish and save the debate scores.

4. **View Dashboard**

   Access `/dashboard` to see your debate scores and performance metrics.

## Contributing

Feel free to fork the repository and submit pull requests. For major changes, please open an issue to discuss the proposed changes.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

Make sure to replace the image file names and paths with those that match your actual images and structure. You can place your images in a folder named `images` in the root of your repository.
