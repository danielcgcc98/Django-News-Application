# Django News Application

A Django news application with Reader, Journalist and Editor roles, publisher subscriptions, article approval, approval notifications, newsletters, MariaDB support and a token-authenticated REST API.

## Requirements

- Python 3.12+
- MariaDB 10.6+
- Git
- Docker Desktop (only for running the app in Docker)
- A MariaDB user/database for the application

## 1. Clone the project

```bash
git clone https://github.com/danielgc98/Django-News-Application.git
cd Django-News-Application
```

If you are working from the submitted ZIP instead, extract the project and open a terminal in the folder containing `manage.py`.

## 2. Create and activate a virtual environment

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

The project uses Django, Django REST Framework, mysqlclient, requests and python-dotenv.

## 4. Create the MariaDB database and user

Log in to MariaDB and run:

```sql
CREATE DATABASE news_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'news_user'@'localhost' IDENTIFIED BY 'replace-with-your-mariadb-password';
GRANT ALL PRIVILEGES ON news_db.* TO 'news_user'@'localhost';
FLUSH PRIVILEGES;
```

Use your own secure password.

## 5. Configure environment variables

Copy `.env.example` to `.env`:

macOS/Linux:

```bash
cp .env.example .env
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Edit `.env` and set:

```text
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost

DB_NAME=news_db
DB_USER=news_user
DB_PASSWORD=your-mariadb-password
DB_HOST=127.0.0.1
DB_PORT=3306
```

The project loads `.env` automatically using `python-dotenv`.

## 6. Run migrations

```bash
python manage.py migrate
```

This creates the Django tables and the News application tables in MariaDB.

The `post_migrate` hook creates the Reader, Journalist and Editor groups and assigns their model permissions.

## 7. Create an administrator

```bash
python manage.py createsuperuser
```

Follow the prompts.

## 8. Run the automated tests

```bash
python manage.py test
```

The test suite covers successful and failed requests for authentication, article access, article CRUD, editor approval, subscriptions, newsletters, email notification and REST API role restrictions.

## 9. Start the development server

```bash
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/
```

Register users with the Reader, Journalist or Editor role.

## 10. Run the application with Docker

The Docker image contains the Django application only. It connects to the
MariaDB server that is already running on your computer, so complete steps
4 to 7 above first (database, user, `.env` file and migrations).

The `.env` file is never copied into the image (see `.dockerignore`); it is
passed to the container when it starts.

Build the image from the folder containing the `Dockerfile`:

```bash
docker build -t django-news-app .
```

Run the container:

```bash
docker run --rm -p 8000:8000 --env-file .env \
  -e DB_HOST=host.docker.internal \
  django-news-app
```

`DB_HOST=host.docker.internal` lets the container reach MariaDB on the host
machine. Open:

```text
http://127.0.0.1:8000/
```

Stop the container with `Ctrl+C`.

If MariaDB rejects the connection from Docker, allow the application user to
connect from the container network (run as a MariaDB administrator):

```sql
CREATE USER IF NOT EXISTS 'news_user'@'%' IDENTIFIED BY 'your-mariadb-password';
GRANT ALL PRIVILEGES ON news_db.* TO 'news_user'@'%';
FLUSH PRIVILEGES;
```

## 11. Documentation (Sphinx)

Generated HTML documentation is included in `docs/_build/html/`.
Open `docs/_build/html/index.html` in a browser.

To rebuild it, activate the virtual environment and run:

```bash
pip install sphinx
cd docs
make html
```

`docs/conf.py` loads Django with `DJANGO_SETTINGS_MODULE=news_project.settings`
so the code reference is generated from the project's docstrings.

## User roles

### Reader

- View approved articles.
- View newsletters.
- Subscribe to publishers and journalists through the API.
- Cannot create, edit, delete or approve articles.
- Cannot create, edit or delete newsletters.

### Journalist

- Create articles.
- View and edit their own articles.
- Delete their own articles.
- Create, view, edit and delete their own newsletters.
- Articles created or edited by journalists require editor approval.

### Editor

- View articles, including pending articles.
- Approve articles.
- Edit and delete articles.
- Create, edit and delete newsletters.
- Approval emails are sent to subscribers.

## REST API

All API endpoints require token authentication unless otherwise noted.

### Obtain a token

```text
POST /api/token/
```

Example form data:

```text
username=your_username
password=your_password
```

Use the returned token as:

```text
Authorization: Token YOUR_TOKEN
```

### Article endpoints

```text
GET    /api/articles/
GET    /api/articles/subscribed/
GET    /api/articles/<id>/
POST   /api/articles/
PUT    /api/articles/<id>/
DELETE /api/articles/<id>/
```

Only journalists can create articles. Editors and journalists can update/delete articles, with journalists restricted to their own articles. Readers can retrieve approved content.

### Subscription endpoints

```text
POST   /api/subscribe/journalist/<user_id>/
DELETE /api/subscribe/journalist/<user_id>/
POST   /api/subscribe/publisher/<publisher_id>/
DELETE /api/subscribe/publisher/<publisher_id>/
```

Only readers can subscribe or unsubscribe.

### Newsletter endpoints

```text
GET    /api/newsletters/
POST   /api/newsletters/
GET    /api/newsletters/<id>/
PUT    /api/newsletters/<id>/
DELETE /api/newsletters/<id>/
```

Readers can view newsletters. Journalists and editors can create newsletters. Journalists can manage their own newsletters; editors can manage newsletters.

### Approval logging endpoint

```text
POST /api/approved/
```

The website's editor approval view uses Python `requests` to POST an approval event to this endpoint. The endpoint records the event through the application's logger.

## Website newsletter pages

```text
/newsletters/
/newsletter/create/
/newsletter/<id>/
/newsletter/<id>/edit/
/newsletter/<id>/delete/
```

Readers can view newsletters. Journalists and editors can manage newsletters according to their role.

## Article approval workflow

1. A journalist creates an article.
2. The article starts as unapproved.
3. An editor reviews the pending article.
4. The editor submits the approval form.
5. The article is marked approved.
6. Subscribers to the journalist and/or publisher are emailed.
7. The approval view sends a POST request to `/api/approved/` using the editor's DRF token.
8. API logging failures are caught and logged so they do not undo the approval.

## Project structure

```text
Django-News-Application/
├── manage.py
├── requirements.txt
├── README.md
├── Dockerfile
├── .dockerignore
├── .env.example
├── docs/                 Sphinx source and generated HTML (docs/_build/html)
├── news_project/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── news/
│   ├── models.py
│   ├── views.py
│   ├── api_views.py
│   ├── serializers.py
│   ├── forms.py
│   ├── signals.py
│   ├── tests.py
│   ├── admin.py
│   ├── urls.py
│   ├── migrations/
│   └── templates/
└── templates/
    └── registration/
```

## Notes

- `.env` is intentionally not included in the repository or submission. Use `.env.example` as the template.
- Database credentials and Django secret keys should never be committed.
- The project uses MariaDB rather than SQLite for the application database.

## Front-end management workflows

### Publisher management
Editors use **Publishers** in the navigation and choose **Create Publisher**. The publisher form lets an editor enter the publisher name and assign editors and journalists. The editor creating the publisher is automatically assigned as an editor. Editors can also edit or delete publishers from the publisher list. The publisher list displays the current journalist/editor assignments.

### Article creation and independent articles
Journalists choose **Create Article** from the navigation. The form clearly displays the article title, content, and optional publisher fields. Selecting **Independent article (no publisher)** allows the journalist to create an article without a publisher. The optional independent approval checkbox can publish an independent article immediately; publisher-linked articles remain pending editor approval. Journalists can edit and delete their own articles; editors can edit and delete any article.

### Newsletter management
Journalists and editors can choose **Create Newsletter**. The article selection is filtered to approved articles only. Newsletter list/detail pages show Edit and Delete controls to authorized users. Journalists can manage their own newsletters; editors can manage newsletters.

### Reader subscriptions
Readers choose **My Subscriptions** in the navigation. This page provides Subscribe/Unsubscribe controls for every journalist and publisher. The actions update the same subscription relationships used by the API and article approval notifications.

## Main website routes

```text
/
/accounts/register/
/article/create/
/article/<id>/edit/
/article/<id>/delete/
/publishers/
/publisher/create/
/publisher/<id>/edit/
/publisher/<id>/delete/
/newsletters/
/newsletter/create/
/newsletter/<id>/edit/
/newsletter/<id>/delete/
/subscriptions/
```
