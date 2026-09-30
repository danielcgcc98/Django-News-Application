# Django News Application

A Django news application with custom user roles, publisher subscriptions, article approval, email notifications, newsletters, and a Django REST Framework API.

## Project structure

- `news/` - application code, models, views, forms, serializers, API views, tests and templates.
- `news_project/` - Django project configuration.
- `templates/registration/` - authentication templates, including login and registration.
- `requirements.txt` - Python dependencies.
- `.gitignore` - excludes virtual environments, databases, secrets and generated files.

## Requirements

- Python 3.12+
- MariaDB 10.6+ (or a compatible MariaDB installation)
- Git

## Clone and install

```bash
git clone REPLACE_WITH_YOUR_GITHUB_REPOSITORY_URL
cd Django_News_Application
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

On Windows, activate the virtual environment with `venv\Scripts\activate`.

## Create the MariaDB database

Start MariaDB, then open the MariaDB client:

```bash
sudo mysql
```

Run the following SQL. Replace `CHANGE_THIS_PASSWORD` with the password you want to use for the Django database user:

```sql
CREATE DATABASE news_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'news_user'@'localhost' IDENTIFIED BY 'CHANGE_THIS_PASSWORD';
GRANT ALL PRIVILEGES ON news_db.* TO 'news_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

If the user or database already exists, use the existing account rather than creating it again.

## Configure environment variables

Copy `.env.example` to `.env`, edit the values, and load them into the shell before running Django. For example:

```bash
cp .env.example .env
# Edit .env with your database password and secret key
set -a
source .env
set +a
```

The variables loaded from `.env` are then used by Django. For example:

```bash
export DJANGO_SECRET_KEY='replace-with-your-secret-key'
export DJANGO_DEBUG='True'
export DJANGO_ALLOWED_HOSTS='127.0.0.1,localhost'
export DB_NAME='news_db'
export DB_USER='news_user'
export DB_PASSWORD='CHANGE_THIS_PASSWORD'
export DB_HOST='127.0.0.1'
export DB_PORT='3306'
```

The `.env` file itself is ignored by Git and should not be committed.

## Run migrations

```bash
python manage.py check
python manage.py makemigrations
python manage.py migrate
```

Create an administrator if required:

```bash
python manage.py createsuperuser
```

## Run the application

```bash
python manage.py runserver
```

Open `http://127.0.0.1:8000/`. New users can use the registration link on the login page.

## User roles

The application supports Reader, Journalist and Editor roles. Registration assigns the selected role and synchronizes the corresponding Django group.

- **Reader:** can view approved articles and use subscription functionality.
- **Journalist:** can create, edit and delete their own articles.
- **Editor:** can review pending articles and approve them.

## REST API

Token authentication is available at:

`POST /api/token/`

The article and newsletter API endpoints are documented by their route names in `news/urls.py`. Use a token in the request header:

```text
Authorization: Token YOUR_TOKEN
```

## Testing

Run the automated tests with:

```bash
python manage.py test
```

## GitHub workflow

After creating your personal GitHub repository, add the remote and push the project:

```bash
git init
git add .
git commit -m "Initial Django News Application"
git branch -M main
git remote add origin REPLACE_WITH_YOUR_GITHUB_REPOSITORY_URL
git push -u origin main
```

Do not commit `venv/`, database files, `.env`, or other generated files.
