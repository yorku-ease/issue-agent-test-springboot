# issue-agent-test-springboot

Spring Boot microservices test repository for the issue-agent system.

## Services

| Service | Port | Description |
|---------|------|-------------|
| `api-gateway` | 8080 | Spring Cloud Gateway — routes all requests |
| `user-service` | 8081 | User registration, authentication, JWT |
| `order-service` | 8082 | Order creation and management |
| `notification-service` | 8084 | Email notifications |

## Key files for co-change testing

- `user-service/.../service/UserService.java` — touched by PRs fixing auth bugs
- `user-service/.../security/JwtUtil.java` — touched by PRs fixing token issues
- `order-service/.../service/OrderService.java` — touched by PRs fixing order bugs
- `order-service/.../controller/OrderController.java` — touched by PRs fixing HTTP status
- `notification-service/.../service/NotificationService.java` — touched by exception handling PR
- `api-gateway/src/main/resources/application.yml` — touched by gateway config PR

## Running locally

```bash
cd user-service && mvn spring-boot:run
cd order-service && mvn spring-boot:run
cd notification-service && mvn spring-boot:run
cd api-gateway && mvn spring-boot:run
```
