# Marketplace Project

## Introduction
This is a simple marketplace application built with Django. Users can sign up, create ads, engage in transactions, and chat with others.

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/username/repo.git
    ```

2. Create a virtual environment:
    ```bash
    python3 -m venv env
    ```

3. Activate the virtual environment:
    - On Windows:
      ```bash
      .\env\Scripts\activate
      ```
    - On macOS/Linux:
      ```bash
      source env/bin/activate
      ```

4. Install the requirements:
    ```bash
    pip install -r requirements.txt
    ```

5. Apply migrations:
    ```bash
    python manage.py migrate
    ```

6. Create a superuser:
    ```bash
    python manage.py createsuperuser
    ```

7. Run the development server:
    ```bash
    python manage.py runserver
    ```

## Features
- User registration and authentication
- Ad creation and management
- Transactions with escrow feature
- Real-time chat between users

## License
This project is licensed under the MIT License.
