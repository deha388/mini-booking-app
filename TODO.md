# Mini Booking System - Todo List

## 1. Project Setup and Environment Preparation
- [x] Create Django project (e.g. "django-admin startproject mini_booking")
- [x] Create Django app named "booking" ("python manage.py startapp booking")
- [x] Create virtual environment and isolate dependencies
- [x] Initialize Git repository and make first commit
- [x] Add Django, psycopg2 and other required packages to requirements.txt

## 2. User Registration and Authentication
- [x] Integrate Django's built-in auth system (login, logout, registration)
- [x] Create templates and URLs for user registration, login and logout

## 3. Facility Model Creation
- [x] Create Facility model (fields: name, location, capacity)
- [x] Apply model changes to database with migrate commands

## 4. Booking Model Creation
- [x] Create Booking model (fields: user, facility, date, status)
- [x] Create model in database using migrate

## 5. Booking Creation with Django Forms
- [x] Create Django Form or ModelForm for Booking
- [x] Add form validation and business rules

## 6. Reservation Management with Class-Based Views (CBVs)
- [x] Create CBVs for reservation listing, detail, creation, update and deletion
- [x] Implement appropriate URL configuration

## 7. Basic Templates for Facility and Reservation Listing
- [x] Create basic HTML templates to display Facility and Booking lists
- [x] (Optional) Add Bootstrap/Tailwind for UI improvements

## 8. Admin Panel Customization (Optional)
- [x] Customize Facility and Booking models in Django admin panel
- [x] Add list filters, search fields and editing options

## 9. Unit Tests
- [x] Write tests for models, views and forms
- [x] Cover user registration, reservation creation and form validation scenarios

## 10. Database Optimizations
- [x] Create indexes for frequently queried fields
- [x] Watch out for N+1 query problems and optimize queries
- [x] Apply database constraints like unique, not null where needed

## 11. Containerization with Docker
- [x] Create Dockerfile for Django application
- [x] Create docker-compose.yml configuration for PostgreSQL database and Django backend
- [x] (Optional) Manage environment variables with .env file
- [x] Detail setup steps in README.md (e.g. "docker-compose up")

## 12. Optional Bonus Features
- [x] Develop asynchronous reservation form with AJAX
- [x] Add background tasks with Celery (e.g. reservation confirmation emails)
- [x] (Optional) Create Custom User Model
- [x] (Optional) Use Bootstrap/Tailwind for advanced CSS and UI
- [x] (Optional) Add health check endpoint for Docker container monitoring

## 13. Final Checks and GitHub Upload
- [ ] Summarize project setup, technologies used, design decisions and development process in README.md
- [ ] Code review and cleanup (comments, documentation)
- [ ] Push project to GitHub and prepare submission link 