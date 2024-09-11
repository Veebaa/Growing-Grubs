# Process Documentation

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
- Frontend: HTML, CSS, JavaScript files located in the static and templates directories.
- Backend: Python files utilizing Flask framework, stored in the app directory.

#### 3. Dependencies:
- Python: Flask, Requests.
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
- Write unit tests for Flask routes and business logic.
- Use pytest or unittest frameworks for testing.

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
- Integrate automated tests into the CI/CD pipeline.
- Ensure tests are run on each code commit and pull request.

#### 2. Deployment:
- Deploy the application to a staging environment for final testing.
- Use automated deployment scripts for production release.

## 4. Maintenance Procedures
### 4.1. Bug Fixes
#### 1. Issue Tracking:
- Track bugs and issues using an issue tracker (e.g., Jira, GitHub Issues).
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