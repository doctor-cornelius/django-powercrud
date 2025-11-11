# Dockerized Development Environment

## TL;DR - Quick Start

**Just want to get started?**

```bash
./runproj up          # Start all containers (drops you into Django container)
./manage.py migrate   # Set up database
./rs                  # Start Django server (in separate terminal: ./runproj exec)
```

Visit http://localhost:8001 for Django, http://localhost:5174 for Vite assets.

When done: `./runproj down`

---

## Overview

This project uses a multi-container Docker setup for development to provide a complete, isolated environment with all necessary services. This approach enables testing of advanced features like async operations, database concurrency, and real-time asset compilation without complex local installations.

## The `runproj` Script

The `runproj` script simplifies Docker Compose commands:

- `./runproj up [dev]` - Start all containers and exec into Django container
- `./runproj down [dev]` - Stop all containers  
- `./runproj exec` - Exec into running Django container (new terminal)
- `./runproj postgres` - Exec into PostgreSQL container
- `./runproj pgadmin` - Exec into pgAdmin container

## Architecture

The development environment consists of five main services:

=== "Core Services"

    **🐍 Django Application (`django_powercrud_django`)**

    - Main application container running Django
    - Syncs all Python dependencies with `uv` during the image build
    - Mounts project directory for live code changes
    - Exposes port 8001 for web access

    **🗄️ PostgreSQL Database (`django_powercrud_postgres`)**

    - Production-grade database for testing concurrency scenarios
    - Enables proper testing of async features and database locks
    - Persistent data storage via Docker volumes
    - Exposes port 5432 for direct database access

=== "Development Tools"

    **⚡ Vite Dev Server (`django_powercrud_vite`)**

    - Dedicated container for frontend asset compilation
    - Hot Module Replacement (HMR) for instant CSS/JS updates
    - Tailwind CSS compilation with live reloading
    - Exposes port 5174 for browser and Django access

    **🔧 pgAdmin (`pgadmin`)**

    - Web-based PostgreSQL administration tool
    - Visual database management and query interface
    - Accessible at http://localhost:5050
    - Pre-configured with connection details

=== "Async Support"

    **📦 Redis Cache (`redis`)**

    - In-memory data store for caching and session management
    - Available for `django-q2` backend if specified
    - Future-ready for Celery task queue integration
    - Password-protected for security
    - Exposes port 6379

    **🧵 Q2 Worker (`django_powercrud_q2`)**

    - Runs `manage.py qcluster` so async tasks are always available
    - Shares the project volume and uv-managed dependencies with the Django container
    - Restarts automatically alongside Redis and PostgreSQL

## Why Docker for Development?

### 1. **Advanced Database Testing**

- **PostgreSQL vs SQLite**: Test real-world database behavior, constraints, and concurrency
- **Async Operations**: Properly test django-q2 async tasks with database connections
- **Connection Pooling**: Test multiple database connections and transaction isolation

### 2. **Redis Integration**

- **Session Storage**: Test session-based features like bulk selections
- **Caching**: Evaluate caching strategies for large datasets
- **Future Celery Support**: Ready for background task processing

### 3. **Asset Pipeline Isolation**

- **Vite Container**: Frontend builds don't interfere with backend processes  
- **Hot Reloading**: Instant CSS/JS updates without manual rebuilds
- **Framework Testing**: Easy switching between CSS frameworks (Bootstrap ↔ daisyUI)

### 4. **Development Consistency**

- **Environment Parity**: Same versions across all development machines
- **Dependency Isolation**: No conflicts with local Python/Node installations
- **Easy Onboarding**: New developers get full environment with single command

## Development Workflow

### 1. **Start Development Environment**

```bash
./runproj up
```

This command:

- Builds Django container with all dependencies
- Starts PostgreSQL with persistent data
- Initializes Redis with password protection
- Launches Vite dev server with HMR
- Starts pgAdmin for database management
- **Automatically places you inside the Django container**

### 2. **Set Up Django Application**

```bash
# You're now inside the Django container
./manage.py makemigrations
./manage.py migrate
```

### 3. **Start Django Development Server**

```bash
./rs  # Shortcut for ./manage.py runserver 0:8001
```

### 4. **Working in Multiple Terminals**

For additional Django container access (new terminal window):

```bash
./runproj exec  # Opens new bash session in Django container
```

### 5. **Dependency Management with `uv`**

- Dependencies are installed into the system Python via `uv` during the Docker build.
- To refresh them manually inside the container (after editing `pyproject.toml` or `uv.lock`), run:

  ```bash
  uv sync --all-extras
  ```

- The Playwright browsers are cached in `/usr/local/ms-playwright`, so re-running the sync does not redownload them unless the Playwright version changes.

### 6. **Testing Async Features** 

In a separate terminal (after `./runproj exec`):

```bash
./manage.py qcluster  # Start async task processor for django-q2
```

### 7. **Git Workflow**

Commitizen is installed for conventional commits:

```bash
git add -A
cz commit  # Interactive conventional commit
```

### 8. **Shutdown**

```bash
./runproj down  # Stops and removes all containers
```

## Service Access

- **Django App**: http://localhost:8001
- **Vite Dev Server**: http://localhost:5174 (auto-connected to Django)
- **pgAdmin**: http://localhost:5050 (`admin@admin.com` / `admin`)
- **Database**: `localhost:5432` (`postgres` / `Testing123`)

## Container Communication

### Internal Network

- **Django ↔ PostgreSQL**: `django_powercrud_postgres_dev:5432`
- **Django ↔ Redis**: `redis:6379` 
- **Django ↔ Vite**: `localhost:5174` (via host networking)

### External Access

- **Host → Django**: `localhost:8001`
- **Host → Vite**: `localhost:5174` 
- **Host → Database**: `localhost:5432`
- **Browser → Vite**: `localhost:5174` (for HMR)

## Volume Mounts

### Development Volumes

```yaml
volumes:
  - "${PWD}:/home/devuser/django_powercrud"     # Live code editing
  - "/home/devuser/django_powercrud/node_modules"  # Preserve npm packages
  - "${HOME}/.ssh:/home/devuser/.ssh"               # Git authentication
  - "${HOME}/.gitconfig:/home/devuser/.gitconfig"   # Git configuration
```

### Persistent Data

```yaml
volumes:
  - django_powercrud_pgdata:/var/lib/postgresql/data  # Database persistence
  - redis_data:/data                                      # Redis persistence  
  - pgadmin-data:/var/lib/pgadmin                        # pgAdmin settings
```

## Environment Variables

Key configuration stored in `docker/dev/dev.secret`:

```bash
# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=Testing123
DATABASE_NAME=django_powercrud_postgres_dev

# pgAdmin
PGADMIN_DEFAULT_EMAIL=admin@admin.com
PGADMIN_DEFAULT_PASSWORD=admin

# Redis  
REDIS_PASSWORD=redis_password_dev
```

## Async Development Features

### Django-Q2 Integration

```bash
# In Django container
./manage.py qcluster  # Start async task processor
```

### Database Concurrency Testing

- Multiple database connections via PostgreSQL
- Transaction isolation testing
- Async query execution with proper connection handling

### Future Celery Integration

- Redis already configured as message broker
- Container architecture ready for Celery workers
- Separate containers for different worker types

## Troubleshooting

### Common Issues

**Vite Assets Not Loading**

```bash
# Check Vite container status
docker logs django_powercrud_vite_dev

# Restart Vite service
docker restart django_powercrud_vite_dev
```

**Database Connection Failed**

```bash
# Check PostgreSQL status
docker logs django_powercrud_postgres_dev

# Verify database exists
./runproj postgres
# In container: psql -U postgres -l
```

**Port Conflicts**

```bash
# Check which ports are in use
./runproj down  # Stop all services
./runproj up    # Restart with fresh port allocation
```

### Performance Optimization

**For Apple Silicon Macs:**

```yaml
# Add to docker-compose.yml services
platform: linux/amd64  # If needed for compatibility
```

**For Windows WSL:**

```yaml
# Ensure proper volume mounting
watch:
  usePolling: true  # Already configured in vite.config.mjs
```
