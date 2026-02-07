---
name: Backend Development Best Practices
description: A comprehensive guide to building robust, scalable, and maintainable backend systems.
---

# Backend Development Best Practices

This skill outlines key principles and practices for modern backend development.

## 1. API Design (REST & GraphQL)

### RESTful Principles
- **Resource Oriented**: URLs should represent resources (nouns), not actions (verbs).
  - Bad: `/getUsers`, `/createUser`
  - Good: `GET /users`, `POST /users`
- **HTTP Methods**: Use methods correctly:
  - `GET`: Retrieve data (safe, idempotent).
  - `POST`: Create new resources.
  - `PUT`: Update/Replace a resource (idempotent).
  - `PATCH`: Partial update.
  - `DELETE`: Remove a resource.
- **Status Codes**: Return appropriate HTTP status codes.
  - `200 OK`, `201 Created`
  - `400 Bad Request`, `401 Unauthorized`, `403 Forbidden`, `404 Not Found`
  - `500 Internal Server Error`

### GraphQL
- Use when clients need flexible data fetching.
- Prevent N+1 problems using DataLoaders.
- Implement complexity limits to prevent DoS attacks via deep queries.

## 2. Database Management

### Schema Design
- **Normalization vs. Denormalization**: Normalize to reduce redundancy, denormalize for read performance when necessary.
- **Indexes**: Index columns used in `WHERE`, `JOIN`, and `ORDER BY` clauses. Monitor query performance.
- **Migrations**: Always use version control for database schemas (e.g., Alembic, Flyway, Prisma).

### Reliability
- **Connection Pooling**: Use connection pools (e.g., PgBouncer, HikariCP) to manage database connections efficiently.
- **Transactions**: Use transactions for atomicity (ACID properties) when performing multiple related writes.

## 3. Error Handling & Logging

- **Structured Logging**: Log in JSON format for easy parsing and querying (e.g., using ELK stack, Datadog).
- **Context**: Include request IDs, user IDs, and timestamps in all logs.
- **Levels**: Use appropriate log levels (`DEBUG`, `INFO`, `WARN`, `ERROR`).
- **Global Error Handler**: Catch unhandled exceptions at a high level and return generic error messages to the client while logging the stack trace internally.

## 4. Security

- **Authentication & Authorization**:
  - Use modern standards like OAuth2 and OpenID Connect.
  - Use JWTs (JSON Web Tokens) for stateless authentication, but be wary of revocation issues.
  - Implement RBAC (Role-Based Access Control) or ABAC (Attribute-Based Access Control).
- **Input Validation**: Validate all inputs at the boundary. sanitize data to prevent SQL injection and XSS.
- **Rate Limiting**: Protect your API from abuse using rate limiters (e.g., Redis-based token bucket).
- **HTTPS**: Enforce HTTPS everywhere.

## 5. Performance & Scalability

- **Caching**:
  - **Client-side**: Use HTTP caching headers (`Cache-Control`, `ETag`).
  - **Server-side**: Cache expensive database queries or computations using Redis or Memcached.
- **Asynchronous Processing**: Offload long-running tasks (emails, report generation) to background queues (e.g., Celery, Bull, Kafka).

## 6. Testing

- **Unit Tests**: Test individual functions/classes in isolation.
- **Integration Tests**: Test interactions between components (API -> DB).
- **E2E Tests**: Test critical user flows.
- **CI/CD**: Run tests automatically on every commit.
