---
name: System Design Fundamentals
description: Core concepts and patterns for designing scalable distributed systems.
---

# System Design Fundamentals

This skill covers the essential concepts needed to design scalable, reliable, and maintainable systems.

## 1. Core Concepts

### Scalability
- **Vertical Scaling (Scale Up)**: Adding more power (CPU, RAM) to an existing machine. Limited by hardware capacity.
- **Horizontal Scaling (Scale Out)**: Adding more machines to the resource pool. Theoretical unlimited scaling, but adds complexity.

### Availability & Reliability
- **Redundancy**: eliminating single points of failure.
- **Replication**: Storing data on multiple machines.
- **Load Balancing**: Distributing traffic across multiple servers (L4 transport layer vs L7 application layer).

### CAP Theorem
In a distributed data store, you can only provide two of the following three guarantees:
- **Consistency**: Every read receives the most recent write or an error.
- **Availability**: Every request receives a (non-error) response, without the guarantee that it contains the most recent write.
- **Partition Tolerance**: The system continues to operate despite an arbitrary number of messages being dropped (or delayed) by the network between nodes.
*Note: In presence of a partition (P), you must choose between C and A.*

## 2. Database Scaling

### Sharding (Data Partitioning)
Splitting a database into smaller, faster, more easily managed parts called shards.
- **Horizontal Partitioning**: Split by rows (e.g., User IDs 1-1000 in DB1, 1001-2000 in DB2).
- **Shard Key**: Critical choice. Bad keys lead to "hot spots".
- **Consistent Hashing**: A technique to minimize reorganization of keys when nodes are added or removed.

### Replication Models
- **Master-Slave**: Master handles writes, Slaves handle reads. Good for read-heavy systems.
- **Master-Master**: Multiple masters handle writes. Complex conflict resolution needed.

## 3. Caching Strategies

- **Cache-Aside (Lazy Loading)**: Application loads data from cache. If missing, loads from DB and updates cache.
- **Write-Through**: Application writes to cache and DB synchronously. Data consistency is high, but write latency is higher.
- **Write-Back (Write-Behind)**: Application writes to cache only. Cache writes to DB asynchronously. Low latency, risk of data loss on crash.

## 4. Communication Protocols

- **HTTP/REST**: Standard, easy to use text-based.
- **gRPC**: High performance, uses Protocol Buffers (binary), supports streaming. Good for internal microservices.
- **WebSockets**: Full-duplex communication channels over a single TCP connection. Real-time apps.
- **Message Queues**: Decoupling services (Kafka, RabbitMQ, SQS). Asynchronous processing.

## 5. Common Patterns

- **Microservices**: Decomposing a monolith into small, loosely coupled services. Independently deployable.
- **API Gateway**: Entry point for all clients. Handles routing, authentication, rate limiting.
- **Circuit Breaker**: Prevents an application from repeatedly trying to execute an operation that's likely to fail.

## 6. System Design Interview Framework

1.  **Requirement Clarification**: Functional & Non-functional requirements (DAU, latency, consistency).
2.  **Back-of-the-Envelope Estimation**: Storage, Bandwidth, QPS estimations.
3.  **High-Level Design**: Abstract API, diagram with key components.
4.  **Deep Dive**: Data model, specific components, edge cases.
5.  **Wrap Up**: Bottlenecks, failure modes, monitoring.
