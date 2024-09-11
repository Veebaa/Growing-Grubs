# Process Documentation

## Table of Contents
1. [Overview](#1-overview)
2. [Development Process](#2-development-process)
3. [Testing Process](#3-testing-process)
4. [Maintenance Procedures](#4-maintenance-procedures)
5. [Documentation and Diagrams](#5-documentation-and-diagrams)
6. [Testing Routes and Functionalities](#6-testing-routes-and-functionalities)


## 1. Overview
This document provides a detailed overview of the processes and procedures used in the development, testing, and
maintenance of the web application. The application leverages Flask for the backend and uses HTML, CSS, and
JavaScript for the frontend. Markdown with Mermaid diagrams are used for documentation and modeling.

## 2. Development Process
### 2.1. Setup and Configuration
#### 1. Development Environment:
- IDE: PyCharm with Mermaid plugin for diagram rendering.
- Version Control: Git for source code management.

#### 2. Codebase Structure:
- Frontend: HTML, CSS, JavaScript files located in the `static` and `templates` directories.
- Backend: Python files utilizing Flask framework, stored in the `app` directory.

#### 3. Dependencies:
- Python: Flask, Requests, Flask-Login, SQLAlchemy 2.0.
- Frontend: Font Awesome for icons.

### 2.2. Development Procedures
#### 1. Feature Development:
- Develop features following the MVC architecture.
- Implement backend routes and logic in Flask.
- Update HTML templates and CSS files for frontend changes.
- Write JavaScript for interactive elements and API integration.

#### 2. Code Reviews:
- Conduct code reviews to ensure adherence to coding standards.
- Use pull requests and review feedback to improve code quality.

#### 3. Documentation:
- Maintain up-to-date documentation for code, APIs, and system architecture.
- Use Mermaid for visual representation of diagrams.

## 3. Testing Process
### 3.1. Unit Testing
#### 1. Backend Tests:
- Write unit tests for Flask routes (see section 6) and business logic.
- Use pytest framework for testing.
- Test Files:
  - `tests/__init__.py`
  - `tests/test_routes.py`
  - `tests/conftest.py`

#### 2. Frontend Tests:
- Perform manual testing of HTML, CSS, and JavaScript functionality.
- Use browser developer tools to inspect and debug issues.

### 3.2. Integration Testing
#### 1. API Testing:
- Test API endpoints using tools like Postman or curl.
- Verify that API responses match the expected format.

#### 2. End-to-End Testing:
- Test the application flow from frontend to backend.
- Validate that all features work seamlessly together.

### 3.3. Continuous Integration
#### 1. Automated Testing:
- For further development, integration of automated tests into the CI/CD pipeline.
- Ensure tests are run on each code commit and pull request.

#### 2. Deployment:
- For further development, deploying the application to a staging environment for final testing.
- Use automated deployment scripts for production release.

## 4. Maintenance Procedures
### 4.1. Bug Fixes
#### 1. Issue Tracking:
- Track bugs and issues using GitHub Issues tracker.
- Prioritize and address critical bugs promptly.

#### 2. Code Fixes:
- Implement fixes and perform regression testing to ensure stability.
- Update documentation to reflect any changes made.

### 4.2. Updates and Enhancements
#### 1. Feature Requests:
- Review and prioritise feature requests from users or stakeholders.
- Develop and test new features in alignment with application goals.

#### 2. Version Management:
- Use semantic versioning for releases.
- Maintain release notes and update documentation for new versions.

### 4.3. Security and Compliance
#### 1. Security Audits:
- Conduct regular security audits to identify and address vulnerabilities.
- Implement security patches and updates as needed.

#### 2. Compliance:
- Ensure the application complies with relevant regulations and standards (e.g., GDPR).

## 5. Documentation and Diagrams
### 5.1. UML Diagrams
- ***User Model***: Describes user attributes and methods.
- ***Favourites Model***: Represents user’s favourite recipes.
- ***Association Table (user_favourites)***: Maps users to their favourite recipes.

### 5.2. Mermaid Diagrams
- ***Class Diagrams***: Provide a visual representation of the system's classes and relationships.
- ***Use Cases***: Document the primary use cases and interactions.
   
### 5.3. Markdown Integration
- Embed Mermaid diagrams in Markdown for visualisation.
- Ensure that Markdown files are kept in sync with the codebase.

## 6. Testing Routes and Functionalities
### 6.1. Login Route
- Route: `/login`
- Method: `POST`
- Description: Handles user authentication and redirects based on login success or failure.
- Testing:
  - Ensure the login form is correctly handled.
  - Test for proper redirection on successful and failed login attempts.

### 6.2. Logout Route
- Route: `/logout`
- Method: `POST`
- Description: Logs the user out and redirects to the homepage.
- Testing:
  - Simulate logout and verify redirection.
  - Ensure only POST requests are accepted.

### 6.3. Profile Route
- Route: `/profile`
- Method: `GET`
- Description: Displays the user’s profile information.
- Testing:
  - Ensure the route displays correct user data after login.
  - Test profile updates and validate changes.

### 6.4. Edit Profile Route
- Route: `/edit_profile`
- Method: `POST`
- Description: Updates the user’s profile information. 
- Testing:
  - Validate form data processing.
  - Verify that user data is updated in the database.

### 6.5. Meal Detail Route
- Route: `/meal/<int:meal_id>`
- Method: `GET`
- Description: Displays detailed information about a specific meal.
- Testing:
  - Ensure correct meal details are rendered.
  - Verify handling of missing or invalid meal IDs.

### 6.6. View Recipe Route
- Route: `/recipe/<int:recipe_id>`
- Method: `GET`
- Description: Redirects to the meal detail page for a specific recipe.
- Testing:
  - Confirm redirection to the correct meal detail page.
  - Test handling of invalid or missing recipe IDs.