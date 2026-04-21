"""
Creates GitHub repo with 10 issues, 10 PRs (all merged), and 4 probe issues.
Usage: GITHUB_TOKEN=<token> python setup_github.py
"""
import os, sys, time, subprocess, requests

TOKEN = os.environ.get("GITHUB_TOKEN", "")
if not TOKEN:
    print("ERROR: Set GITHUB_TOKEN environment variable")
    sys.exit(1)

OWNER = None
REPO = "issue-agent-test-springboot"
BASE = "https://api.github.com"
HEADERS = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


def api(method, path, **kwargs):
    url = f"{BASE}{path}"
    resp = getattr(requests, method)(url, headers=HEADERS, **kwargs)
    if resp.status_code not in (200, 201, 204):
        print(f"  ERROR {resp.status_code} {method.upper()} {path}: {resp.text[:300]}")
        resp.raise_for_status()
    return resp.json() if resp.content else {}


def run(cmd, cwd=None):
    result = subprocess.run(
        cmd, shell=True, cwd=cwd,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    stdout = result.stdout.decode("utf-8", errors="replace") if result.stdout else ""
    stderr = result.stderr.decode("utf-8", errors="replace") if result.stderr else ""
    if result.returncode != 0:
        print(f"  CMD ERROR: {cmd}\n  {stderr}")
        raise RuntimeError(stderr)
    return stdout.strip()


def patch_file(cwd, filepath, content):
    full = os.path.join(cwd, filepath)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)


# ── 1. Get user ────────────────────────────────────────────────────────────
print("Fetching GitHub user...")
user = api("get", "/user")
OWNER = user["login"]
print(f"  Logged in as: {OWNER}")

# ── 2. Create repo ─────────────────────────────────────────────────────────
print(f"\nChecking repo {OWNER}/{REPO}...")
try:
    repo_data = api("post", "/user/repos", json={
        "name": REPO,
        "description": "Spring Boot microservices test repo for issue-agent",
        "private": False,
        "auto_init": False,
    })
    print(f"  Created: {repo_data['html_url']}")
except Exception:
    repo_data = api("get", f"/repos/{OWNER}/{REPO}")
    print(f"  Already exists: {repo_data['html_url']}")

cwd = os.path.dirname(os.path.abspath(__file__))
REPO_URL = f"https://{TOKEN}@github.com/{OWNER}/{REPO}.git"

# ── 3. Push initial commit ─────────────────────────────────────────────────
print("\nChecking remote...")
try:
    run(f'git init', cwd=cwd)
    run(f'git config user.email "xiejohn44@gmail.com"', cwd=cwd)
    run(f'git config user.name "johno"', cwd=cwd)
except Exception:
    pass
try:
    run(f'git remote add origin "{REPO_URL}"', cwd=cwd)
except Exception:
    run(f'git remote set-url origin "{REPO_URL}"', cwd=cwd)
run("git branch -M main", cwd=cwd)
try:
    run("git add -A", cwd=cwd)
    msg_file = os.path.join(cwd, ".git", "COMMIT_MSG_TMP")
    with open(msg_file, "w", encoding="utf-8") as f:
        f.write("Initial Spring Boot microservices structure: user-service, order-service, notification-service, api-gateway")
    run(f'git commit -F "{msg_file}"', cwd=cwd)
except Exception:
    pass
try:
    run("git push -u origin main", cwd=cwd)
    print("  Pushed main branch.")
except Exception:
    print("  Main already pushed, skipping.")

# ── 4. Issues ──────────────────────────────────────────────────────────────
ISSUES = [
    {
        "title": "Bug: UserService.java throws NullPointerException when email is null during registration",
        "body": (
            "## Description\n"
            "When a client calls `POST /api/users/register` without an `email` field, "
            "`UserService.java` passes `null` directly to `userRepository.existsByEmail(null)`, "
            "causing a NullPointerException inside the JPA repository.\n\n"
            "## Steps to reproduce\n"
            "1. `POST /api/users/register` with body `{\"username\": \"alice\", \"password\": \"secret\"}`\n"
            "2. Server throws `NullPointerException` in `UserService.java`\n\n"
            "## Expected\nReturn `400 Bad Request` with a validation message.\n\n"
            "**Affected files:** `user-service/src/main/java/com/example/userservice/service/UserService.java`"
        ),
    },
    {
        "title": "Feature: add @Valid request body validation to UserController.java",
        "body": (
            "## Description\n"
            "`UserController.java` accepts a raw `Map<String, String>` with no validation. "
            "Missing or malformed fields (short passwords, empty usernames) are passed straight "
            "to `UserService.java` without any guard.\n\n"
            "## Proposed solution\n"
            "Introduce a `RegisterRequest` DTO with `@NotBlank`, `@Size`, `@Email` annotations "
            "and annotate the controller method with `@Valid`.\n\n"
            "**Affected files:** `user-service/src/main/java/com/example/userservice/controller/UserController.java`"
        ),
    },
    {
        "title": "Bug: OrderService.java creates order without verifying product exists via ProductClient.java",
        "body": (
            "## Description\n"
            "`OrderService.java:createOrder` saves the order directly to the database without "
            "calling `ProductClient.java:productExists` first. Orders are being placed for "
            "non-existent product IDs, causing downstream failures.\n\n"
            "## Steps to reproduce\n"
            "1. `POST /api/orders` with `productId: 99999`\n"
            "2. Order is saved with status PENDING despite product not existing\n\n"
            "## Fix\nCall `productClient.productExists(productId)` in `OrderService.java` before saving.\n\n"
            "**Affected files:** `order-service/src/main/java/com/example/orderservice/service/OrderService.java`, "
            "`order-service/src/main/java/com/example/orderservice/client/ProductClient.java`"
        ),
    },
    {
        "title": "Bug: api-gateway application.yml missing fallback routes — downstream errors return 500",
        "body": (
            "## Description\n"
            "When `user-service` or `order-service` return 404 or are unavailable, "
            "the gateway in `api-gateway/src/main/resources/application.yml` has no fallback "
            "configured. The gateway returns a raw 500 instead of a meaningful 503/404.\n\n"
            "## Fix\n"
            "Add `default-filters` with `FallbackHeaders` and fallback URIs for each route.\n\n"
            "**Affected files:** `api-gateway/src/main/resources/application.yml`"
        ),
    },
    {
        "title": "Bug: JwtUtil.java does not enforce token expiry — expired tokens are accepted",
        "body": (
            "## Description\n"
            "`JwtUtil.java:validateToken` calls `parseClaimsJws` but does not explicitly check "
            "whether the token's expiry date has passed. The JJWT library will throw "
            "`ExpiredJwtException` only if the signature is also invalid — tokens with valid "
            "signatures but past expiry are silently accepted.\n\n"
            "## Fix\nExplicitly extract the expiry claim and compare to `new Date()` in `JwtUtil.java`.\n\n"
            "**Affected files:** `user-service/src/main/java/com/example/userservice/security/JwtUtil.java`"
        ),
    },
    {
        "title": "Feature: implement JWT refresh token support in JwtUtil.java and UserService.java",
        "body": (
            "## Description\n"
            "Currently `JwtUtil.java` only generates access tokens with a 24-hour expiry. "
            "There is no refresh token mechanism. Users are forced to re-login after expiry.\n\n"
            "## Proposed solution\n"
            "1. Add `generateRefreshToken(String username)` to `JwtUtil.java` with a 7-day expiry\n"
            "2. Add `refreshAccessToken(String refreshToken)` to `UserService.java`\n"
            "3. Store refresh tokens in a `refresh_tokens` table\n\n"
            "**Affected files:** `user-service/src/main/java/com/example/userservice/security/JwtUtil.java`, "
            "`user-service/src/main/java/com/example/userservice/service/UserService.java`"
        ),
    },
    {
        "title": "Bug: OrderController.java returns HTTP 200 instead of 201 on successful order creation",
        "body": (
            "## Description\n"
            "`OrderController.java:createOrder` uses `ResponseEntity.ok()` which returns 200. "
            "REST convention for resource creation is HTTP 201 Created with a `Location` header.\n\n"
            "## Fix\nChange `ResponseEntity.ok(...)` to `ResponseEntity.status(201).body(...)` "
            "and add a `Location` header pointing to the new order URL.\n\n"
            "**Affected files:** `order-service/src/main/java/com/example/orderservice/controller/OrderController.java`, "
            "`order-service/src/main/java/com/example/orderservice/service/OrderService.java`"
        ),
    },
    {
        "title": "Security: UserService.java stores passwords in plaintext — must use BCrypt hashing",
        "body": (
            "## Description\n"
            "`UserService.java:register` stores the raw password string directly: "
            "`user.setPassword(password)`. This is a critical security vulnerability — "
            "any database breach exposes all user passwords.\n\n"
            "## Fix\n"
            "1. Add `BCryptPasswordEncoder` bean\n"
            "2. Encode password in `UserService.java` before saving\n"
            "3. Update `UserController.java` login path to use `passwordEncoder.matches()`\n\n"
            "**Affected files:** `user-service/src/main/java/com/example/userservice/service/UserService.java`, "
            "`user-service/src/main/java/com/example/userservice/controller/UserController.java`"
        ),
    },
    {
        "title": "Bug: NotificationService.java swallows all exceptions — OrderService.java cannot detect email failures",
        "body": (
            "## Description\n"
            "`NotificationService.java:sendOrderConfirmation` catches all exceptions silently. "
            "`OrderService.java` calls this after saving an order but has no way to know "
            "whether the notification was sent. Failed emails go completely undetected.\n\n"
            "## Fix\n"
            "1. Re-throw as `NotificationException` in `NotificationService.java`\n"
            "2. Handle the exception in `OrderService.java` — log it and optionally retry\n\n"
            "**Affected files:** `notification-service/src/main/java/com/example/notificationservice/service/NotificationService.java`, "
            "`order-service/src/main/java/com/example/orderservice/service/OrderService.java`"
        ),
    },
    {
        "title": "Performance: OrderRepository.java N+1 query causes severe slowdown in OrderService.java",
        "body": (
            "## Description\n"
            "`OrderRepository.java:findByUserId` uses a default Spring Data query with no JOIN FETCH. "
            "When `OrderService.java:getOrdersByUser` is called, Hibernate fires one query per order "
            "to load related data, causing N+1 queries and 10-20x slowdown under load.\n\n"
            "## Fix\n"
            "Add `@Query` with `JOIN FETCH` in `OrderRepository.java` and use pagination "
            "in `OrderService.java`.\n\n"
            "**Affected files:** `order-service/src/main/java/com/example/orderservice/repository/OrderRepository.java`, "
            "`order-service/src/main/java/com/example/orderservice/service/OrderService.java`"
        ),
    },
]

print("\nFetching or creating 10 issues...")
existing = api("get", f"/repos/{OWNER}/{REPO}/issues", params={"state": "open", "per_page": 100})
existing_titles = {i["title"]: i["number"] for i in existing}
issue_numbers = []
for issue in ISSUES:
    if issue["title"] in existing_titles:
        num = existing_titles[issue["title"]]
        print(f"  Issue #{num} already exists: {issue['title'][:60]}")
        issue_numbers.append(num)
    else:
        result = api("post", f"/repos/{OWNER}/{REPO}/issues", json=issue)
        issue_numbers.append(result["number"])
        print(f"  Created Issue #{result['number']}: {issue['title'][:60]}")
        time.sleep(0.5)
issue_numbers.sort()

# ── 5. Branch definitions ──────────────────────────────────────────────────
US = "user-service/src/main/java/com/example/userservice"
OS = "order-service/src/main/java/com/example/orderservice"
NS = "notification-service/src/main/java/com/example/notificationservice"
GW = "api-gateway/src/main/resources"

BRANCHES = [
    # ── PR 1: fix UserService NPE on null email ────────────────────────────
    {
        "branch": "fix/user-service-null-email-npe",
        "title": "Fix: guard against null email in UserService.java",
        "body": f"Closes #{issue_numbers[0]}\n\nAdd null check before calling `existsByEmail` in `UserService.java` to prevent NPE.",
        "commit_msg": "Fix NPE in UserService.java when email is null during registration",
        "files": {
            f"{US}/service/UserService.java": """\
package com.example.userservice.service;

import com.example.userservice.model.User;
import com.example.userservice.repository.UserRepository;
import org.springframework.stereotype.Service;

@Service
public class UserService {

    private final UserRepository userRepository;

    public UserService(UserRepository userRepository) {
        this.userRepository = userRepository;
    }

    public User register(String username, String password, String email) {
        if (username == null || username.isBlank()) {
            throw new IllegalArgumentException("Username is required");
        }
        if (email != null && userRepository.existsByEmail(email)) {
            throw new RuntimeException("Email already in use");
        }
        if (userRepository.existsByUsername(username)) {
            throw new RuntimeException("Username already taken");
        }
        User user = new User();
        user.setUsername(username);
        user.setPassword(password); // plaintext — fixed in later PR
        user.setEmail(email);
        user.setRole("USER");
        return userRepository.save(user);
    }

    public User findByUsername(String username) {
        return userRepository.findByUsername(username)
                .orElseThrow(() -> new RuntimeException("User not found: " + username));
    }
}
""",
        },
    },
    # ── PR 2: add @Valid DTO to UserController ─────────────────────────────
    {
        "branch": "feature/user-controller-validation",
        "title": "Feature: add @Valid DTO validation in UserController.java",
        "body": f"Closes #{issue_numbers[1]}\n\nIntroduce `RegisterRequest` DTO with Bean Validation annotations. Annotate controller with `@Valid`.",
        "commit_msg": "Add @Valid DTO validation in UserController.java — reject malformed registration requests",
        "files": {
            f"{US}/dto/RegisterRequest.java": """\
package com.example.userservice.dto;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public class RegisterRequest {
    @NotBlank(message = "Username is required")
    @Size(min = 3, max = 50, message = "Username must be 3-50 characters")
    private String username;

    @NotBlank(message = "Password is required")
    @Size(min = 8, message = "Password must be at least 8 characters")
    private String password;

    @Email(message = "Invalid email format")
    private String email;

    public String getUsername() { return username; }
    public void setUsername(String username) { this.username = username; }
    public String getPassword() { return password; }
    public void setPassword(String password) { this.password = password; }
    public String getEmail() { return email; }
    public void setEmail(String email) { this.email = email; }
}
""",
            f"{US}/controller/UserController.java": """\
package com.example.userservice.controller;

import com.example.userservice.dto.RegisterRequest;
import com.example.userservice.model.User;
import com.example.userservice.service.UserService;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/users")
public class UserController {

    private final UserService userService;

    public UserController(UserService userService) {
        this.userService = userService;
    }

    @PostMapping("/register")
    public ResponseEntity<?> register(@Valid @RequestBody RegisterRequest request) {
        User user = userService.register(
                request.getUsername(),
                request.getPassword(),
                request.getEmail()
        );
        return ResponseEntity.ok(Map.of("id", user.getId(), "username", user.getUsername()));
    }

    @GetMapping("/{username}")
    public ResponseEntity<?> getUser(@PathVariable String username) {
        User user = userService.findByUsername(username);
        return ResponseEntity.ok(Map.of("username", user.getUsername(), "email", user.getEmail()));
    }
}
""",
        },
    },
    # ── PR 3: validate product before order ────────────────────────────────
    {
        "branch": "fix/order-service-product-validation",
        "title": "Fix: verify product exists in OrderService.java via ProductClient.java",
        "body": f"Closes #{issue_numbers[2]}\n\nCall `productClient.productExists()` before saving order. Propagate errors from `ProductClient.java` properly.",
        "commit_msg": "Fix OrderService.java: validate product via ProductClient before creating order",
        "files": {
            f"{OS}/client/ProductClient.java": """\
package com.example.orderservice.client;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.RestTemplate;

@Component
public class ProductClient {

    private static final Logger log = LoggerFactory.getLogger(ProductClient.class);
    private final RestTemplate restTemplate;
    private static final String PRODUCT_SERVICE_URL = "http://product-service:8083";

    public ProductClient(RestTemplate restTemplate) {
        this.restTemplate = restTemplate;
    }

    public boolean productExists(Long productId) {
        try {
            restTemplate.getForObject(PRODUCT_SERVICE_URL + "/api/products/" + productId, Object.class);
            return true;
        } catch (HttpClientErrorException.NotFound e) {
            return false;
        } catch (Exception e) {
            log.error("Error checking product {}: {}", productId, e.getMessage());
            throw new RuntimeException("Product service unavailable", e);
        }
    }

    public Integer getStock(Long productId) {
        try {
            return restTemplate.getForObject(
                    PRODUCT_SERVICE_URL + "/api/products/" + productId + "/stock", Integer.class);
        } catch (Exception e) {
            log.warn("Could not fetch stock for product {}", productId);
            return null;
        }
    }
}
""",
            f"{OS}/service/OrderService.java": """\
package com.example.orderservice.service;

import com.example.orderservice.client.ProductClient;
import com.example.orderservice.model.Order;
import com.example.orderservice.repository.OrderRepository;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.List;

@Service
public class OrderService {

    private final OrderRepository orderRepository;
    private final ProductClient productClient;

    public OrderService(OrderRepository orderRepository, ProductClient productClient) {
        this.orderRepository = orderRepository;
        this.productClient = productClient;
    }

    public Order createOrder(Long userId, Long productId, Integer quantity) {
        if (!productClient.productExists(productId)) {
            throw new RuntimeException("Product not found: " + productId);
        }
        Order order = new Order();
        order.setUserId(userId);
        order.setProductId(productId);
        order.setQuantity(quantity);
        order.setStatus("PENDING");
        order.setCreatedAt(LocalDateTime.now());
        return orderRepository.save(order);
    }

    public List<Order> getOrdersByUser(Long userId) {
        // N+1 still present — fixed in later PR
        return orderRepository.findByUserId(userId);
    }
}
""",
        },
    },
    # ── PR 4: api-gateway fallback routes ──────────────────────────────────
    {
        "branch": "fix/api-gateway-fallback-routes",
        "title": "Fix: add fallback routes and error handling in api-gateway application.yml",
        "body": f"Closes #{issue_numbers[3]}\n\nAdd `default-filters`, fallback URIs, and a `/fallback` endpoint so downstream failures return clean 503 responses.",
        "commit_msg": "Add fallback routes and default error filters to api-gateway/application.yml",
        "files": {
            f"{GW}/application.yml": """\
spring:
  application:
    name: api-gateway
  cloud:
    gateway:
      default-filters:
        - name: CircuitBreaker
          args:
            name: defaultCircuitBreaker
            fallbackUri: forward:/fallback
      routes:
        - id: user-service
          uri: http://user-service:8081
          predicates:
            - Path=/api/users/**
          filters:
            - name: CircuitBreaker
              args:
                name: userServiceCircuitBreaker
                fallbackUri: forward:/fallback/user-service
        - id: order-service
          uri: http://order-service:8082
          predicates:
            - Path=/api/orders/**
          filters:
            - name: CircuitBreaker
              args:
                name: orderServiceCircuitBreaker
                fallbackUri: forward:/fallback/order-service
        - id: notification-service
          uri: http://notification-service:8084
          predicates:
            - Path=/api/notifications/**

resilience4j:
  circuitbreaker:
    instances:
      defaultCircuitBreaker:
        slidingWindowSize: 10
        failureRateThreshold: 50
        waitDurationInOpenState: 10s

server:
  port: 8080
""",
        },
    },
    # ── PR 5: JwtUtil expiry check ─────────────────────────────────────────
    {
        "branch": "fix/jwt-token-expiry",
        "title": "Fix: enforce token expiry in JwtUtil.java",
        "body": f"Closes #{issue_numbers[4]}\n\nExplicitly check expiry date in `validateToken` and catch `ExpiredJwtException` separately.",
        "commit_msg": "Fix JwtUtil.java: explicitly validate token expiry date",
        "files": {
            f"{US}/security/JwtUtil.java": """\
package com.example.userservice.security;

import io.jsonwebtoken.*;
import org.springframework.stereotype.Component;

import java.util.Date;

@Component
public class JwtUtil {

    private static final String SECRET = "mySecretKey12345678901234567890ab";
    private static final long EXPIRY_MS = 86_400_000L; // 24 hours

    public String generateToken(String username) {
        return Jwts.builder()
                .setSubject(username)
                .setIssuedAt(new Date())
                .setExpiration(new Date(System.currentTimeMillis() + EXPIRY_MS))
                .signWith(SignatureAlgorithm.HS256, SECRET)
                .compact();
    }

    public String extractUsername(String token) {
        return Jwts.parser().setSigningKey(SECRET)
                .parseClaimsJws(token).getBody().getSubject();
    }

    public boolean validateToken(String token) {
        try {
            Claims claims = Jwts.parser().setSigningKey(SECRET)
                    .parseClaimsJws(token).getBody();
            return !claims.getExpiration().before(new Date());
        } catch (ExpiredJwtException e) {
            return false;
        } catch (JwtException e) {
            return false;
        }
    }

    public Date getExpiration(String token) {
        return Jwts.parser().setSigningKey(SECRET)
                .parseClaimsJws(token).getBody().getExpiration();
    }
}
""",
        },
    },
    # ── PR 6: JWT refresh token (JwtUtil + UserService) ────────────────────
    {
        "branch": "feature/jwt-refresh-token",
        "title": "Feature: add JWT refresh token to JwtUtil.java and UserService.java",
        "body": f"Closes #{issue_numbers[5]}\n\nAdd `generateRefreshToken` to `JwtUtil.java` (7-day expiry) and `refreshAccessToken` to `UserService.java`.",
        "commit_msg": "Add JWT refresh token support in JwtUtil.java and UserService.java",
        "files": {
            f"{US}/security/JwtUtil.java": """\
package com.example.userservice.security;

import io.jsonwebtoken.*;
import org.springframework.stereotype.Component;

import java.util.Date;

@Component
public class JwtUtil {

    private static final String SECRET = "mySecretKey12345678901234567890ab";
    private static final long ACCESS_EXPIRY_MS  = 86_400_000L;       // 24 hours
    private static final long REFRESH_EXPIRY_MS = 604_800_000L;      // 7 days

    public String generateToken(String username) {
        return buildToken(username, ACCESS_EXPIRY_MS, "access");
    }

    public String generateRefreshToken(String username) {
        return buildToken(username, REFRESH_EXPIRY_MS, "refresh");
    }

    private String buildToken(String username, long expiryMs, String type) {
        return Jwts.builder()
                .setSubject(username)
                .claim("type", type)
                .setIssuedAt(new Date())
                .setExpiration(new Date(System.currentTimeMillis() + expiryMs))
                .signWith(SignatureAlgorithm.HS256, SECRET)
                .compact();
    }

    public String extractUsername(String token) {
        return Jwts.parser().setSigningKey(SECRET)
                .parseClaimsJws(token).getBody().getSubject();
    }

    public boolean validateToken(String token) {
        try {
            Claims claims = Jwts.parser().setSigningKey(SECRET)
                    .parseClaimsJws(token).getBody();
            return !claims.getExpiration().before(new Date());
        } catch (ExpiredJwtException | JwtException e) {
            return false;
        }
    }

    public boolean isRefreshToken(String token) {
        try {
            Claims claims = Jwts.parser().setSigningKey(SECRET)
                    .parseClaimsJws(token).getBody();
            return "refresh".equals(claims.get("type", String.class));
        } catch (JwtException e) {
            return false;
        }
    }

    public Date getExpiration(String token) {
        return Jwts.parser().setSigningKey(SECRET)
                .parseClaimsJws(token).getBody().getExpiration();
    }
}
""",
            f"{US}/service/UserService.java": """\
package com.example.userservice.service;

import com.example.userservice.model.User;
import com.example.userservice.repository.UserRepository;
import com.example.userservice.security.JwtUtil;
import org.springframework.stereotype.Service;

import java.util.Map;

@Service
public class UserService {

    private final UserRepository userRepository;
    private final JwtUtil jwtUtil;

    public UserService(UserRepository userRepository, JwtUtil jwtUtil) {
        this.userRepository = userRepository;
        this.jwtUtil = jwtUtil;
    }

    public User register(String username, String password, String email) {
        if (username == null || username.isBlank()) {
            throw new IllegalArgumentException("Username is required");
        }
        if (email != null && userRepository.existsByEmail(email)) {
            throw new RuntimeException("Email already in use");
        }
        if (userRepository.existsByUsername(username)) {
            throw new RuntimeException("Username already taken");
        }
        User user = new User();
        user.setUsername(username);
        user.setPassword(password); // plaintext — fixed in PR #8
        user.setEmail(email);
        user.setRole("USER");
        return userRepository.save(user);
    }

    public Map<String, String> refreshAccessToken(String refreshToken) {
        if (!jwtUtil.validateToken(refreshToken) || !jwtUtil.isRefreshToken(refreshToken)) {
            throw new RuntimeException("Invalid or expired refresh token");
        }
        String username = jwtUtil.extractUsername(refreshToken);
        String newAccessToken = jwtUtil.generateToken(username);
        return Map.of("accessToken", newAccessToken);
    }

    public User findByUsername(String username) {
        return userRepository.findByUsername(username)
                .orElseThrow(() -> new RuntimeException("User not found: " + username));
    }
}
""",
        },
    },
    # ── PR 7: OrderController 201 + OrderService status ───────────────────
    {
        "branch": "fix/order-controller-http-201",
        "title": "Fix: return HTTP 201 Created in OrderController.java on order creation",
        "body": f"Closes #{issue_numbers[6]}\n\nChange `ResponseEntity.ok()` to `ResponseEntity.status(201)` and add `Location` header. Update `OrderService.java` to return enriched response.",
        "commit_msg": "Fix OrderController.java: return 201 Created with Location header on order creation",
        "files": {
            f"{OS}/controller/OrderController.java": """\
package com.example.orderservice.controller;

import com.example.orderservice.model.Order;
import com.example.orderservice.service.OrderService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.support.ServletUriComponentsBuilder;

import java.net.URI;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/orders")
public class OrderController {

    private final OrderService orderService;

    public OrderController(OrderService orderService) {
        this.orderService = orderService;
    }

    @PostMapping
    public ResponseEntity<?> createOrder(@RequestBody Map<String, Object> request) {
        Order order = orderService.createOrder(
                Long.valueOf(request.get("userId").toString()),
                Long.valueOf(request.get("productId").toString()),
                Integer.valueOf(request.get("quantity").toString())
        );
        URI location = ServletUriComponentsBuilder.fromCurrentRequest()
                .path("/{id}").buildAndExpand(order.getId()).toUri();
        return ResponseEntity.created(location)
                .body(Map.of("id", order.getId(), "status", order.getStatus()));
    }

    @GetMapping("/user/{userId}")
    public ResponseEntity<List<Order>> getOrdersByUser(@PathVariable Long userId) {
        return ResponseEntity.ok(orderService.getOrdersByUser(userId));
    }

    @GetMapping("/{id}")
    public ResponseEntity<?> getOrder(@PathVariable Long id) {
        return ResponseEntity.ok(Map.of("id", id));
    }
}
""",
            f"{OS}/service/OrderService.java": """\
package com.example.orderservice.service;

import com.example.orderservice.client.ProductClient;
import com.example.orderservice.model.Order;
import com.example.orderservice.repository.OrderRepository;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.List;

@Service
public class OrderService {

    private final OrderRepository orderRepository;
    private final ProductClient productClient;

    public OrderService(OrderRepository orderRepository, ProductClient productClient) {
        this.orderRepository = orderRepository;
        this.productClient = productClient;
    }

    public Order createOrder(Long userId, Long productId, Integer quantity) {
        if (!productClient.productExists(productId)) {
            throw new RuntimeException("Product not found: " + productId);
        }
        Order order = new Order();
        order.setUserId(userId);
        order.setProductId(productId);
        order.setQuantity(quantity);
        order.setStatus("CONFIRMED");
        order.setCreatedAt(LocalDateTime.now());
        return orderRepository.save(order);
    }

    public List<Order> getOrdersByUser(Long userId) {
        return orderRepository.findByUserId(userId);
    }
}
""",
        },
    },
    # ── PR 8: BCrypt password (UserService + UserController) ──────────────
    {
        "branch": "fix/bcrypt-password-encoding",
        "title": "Security: encode passwords with BCrypt in UserService.java and UserController.java",
        "body": f"Closes #{issue_numbers[7]}\n\nReplace plaintext password storage with `BCryptPasswordEncoder`. Update login flow in `UserController.java` to use `matches()`.",
        "commit_msg": "Security: BCrypt password hashing in UserService.java, verify with matches() in UserController.java",
        "files": {
            f"{US}/service/UserService.java": """\
package com.example.userservice.service;

import com.example.userservice.model.User;
import com.example.userservice.repository.UserRepository;
import com.example.userservice.security.JwtUtil;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.stereotype.Service;

import java.util.Map;

@Service
public class UserService {

    private final UserRepository userRepository;
    private final JwtUtil jwtUtil;
    private final BCryptPasswordEncoder passwordEncoder = new BCryptPasswordEncoder();

    public UserService(UserRepository userRepository, JwtUtil jwtUtil) {
        this.userRepository = userRepository;
        this.jwtUtil = jwtUtil;
    }

    public User register(String username, String password, String email) {
        if (username == null || username.isBlank()) {
            throw new IllegalArgumentException("Username is required");
        }
        if (email != null && userRepository.existsByEmail(email)) {
            throw new RuntimeException("Email already in use");
        }
        if (userRepository.existsByUsername(username)) {
            throw new RuntimeException("Username already taken");
        }
        User user = new User();
        user.setUsername(username);
        user.setPassword(passwordEncoder.encode(password));
        user.setEmail(email);
        user.setRole("USER");
        return userRepository.save(user);
    }

    public boolean verifyPassword(String rawPassword, String encodedPassword) {
        return passwordEncoder.matches(rawPassword, encodedPassword);
    }

    public Map<String, String> refreshAccessToken(String refreshToken) {
        if (!jwtUtil.validateToken(refreshToken) || !jwtUtil.isRefreshToken(refreshToken)) {
            throw new RuntimeException("Invalid or expired refresh token");
        }
        String username = jwtUtil.extractUsername(refreshToken);
        return Map.of("accessToken", jwtUtil.generateToken(username));
    }

    public User findByUsername(String username) {
        return userRepository.findByUsername(username)
                .orElseThrow(() -> new RuntimeException("User not found: " + username));
    }
}
""",
            f"{US}/controller/UserController.java": """\
package com.example.userservice.controller;

import com.example.userservice.dto.RegisterRequest;
import com.example.userservice.model.User;
import com.example.userservice.security.JwtUtil;
import com.example.userservice.service.UserService;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/users")
public class UserController {

    private final UserService userService;
    private final JwtUtil jwtUtil;

    public UserController(UserService userService, JwtUtil jwtUtil) {
        this.userService = userService;
        this.jwtUtil = jwtUtil;
    }

    @PostMapping("/register")
    public ResponseEntity<?> register(@Valid @RequestBody RegisterRequest request) {
        User user = userService.register(
                request.getUsername(),
                request.getPassword(),
                request.getEmail()
        );
        return ResponseEntity.status(201)
                .body(Map.of("id", user.getId(), "username", user.getUsername()));
    }

    @PostMapping("/login")
    public ResponseEntity<?> login(@RequestBody Map<String, String> request) {
        User user = userService.findByUsername(request.get("username"));
        if (!userService.verifyPassword(request.get("password"), user.getPassword())) {
            return ResponseEntity.status(401).body(Map.of("error", "Invalid credentials"));
        }
        String token = jwtUtil.generateToken(user.getUsername());
        String refreshToken = jwtUtil.generateRefreshToken(user.getUsername());
        return ResponseEntity.ok(Map.of("accessToken", token, "refreshToken", refreshToken));
    }

    @GetMapping("/{username}")
    public ResponseEntity<?> getUser(@PathVariable String username) {
        User user = userService.findByUsername(username);
        return ResponseEntity.ok(Map.of("username", user.getUsername(), "email", user.getEmail()));
    }
}
""",
        },
    },
    # ── PR 9: NotificationService + OrderService exception propagation ─────
    {
        "branch": "fix/notification-exception-propagation",
        "title": "Fix: propagate exceptions from NotificationService.java to OrderService.java",
        "body": f"Closes #{issue_numbers[8]}\n\nRe-throw as `NotificationException` in `NotificationService.java`. Handle in `OrderService.java` with logging and retry.",
        "commit_msg": "Fix NotificationService.java: propagate failures; handle in OrderService.java with retry",
        "files": {
            f"{NS}/service/NotificationService.java": """\
package com.example.notificationservice.service;

import com.example.notificationservice.model.NotificationRequest;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.mail.MailException;
import org.springframework.mail.SimpleMailMessage;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.stereotype.Service;

@Service
public class NotificationService {

    private static final Logger log = LoggerFactory.getLogger(NotificationService.class);
    private final JavaMailSender mailSender;

    public NotificationService(JavaMailSender mailSender) {
        this.mailSender = mailSender;
    }

    public void sendOrderConfirmation(NotificationRequest req) {
        try {
            SimpleMailMessage message = new SimpleMailMessage();
            message.setTo(req.getEmail());
            message.setSubject("Order Confirmation #" + req.getOrderId());
            message.setText(req.getBody());
            mailSender.send(message);
            log.info("Notification sent for order #{}", req.getOrderId());
        } catch (MailException e) {
            log.error("Failed to send notification for order #{}: {}", req.getOrderId(), e.getMessage());
            throw new RuntimeException("Notification delivery failed for order #" + req.getOrderId(), e);
        }
    }
}
""",
            f"{OS}/service/OrderService.java": """\
package com.example.orderservice.service;

import com.example.orderservice.client.ProductClient;
import com.example.orderservice.model.Order;
import com.example.orderservice.repository.OrderRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.List;

@Service
public class OrderService {

    private static final Logger log = LoggerFactory.getLogger(OrderService.class);
    private final OrderRepository orderRepository;
    private final ProductClient productClient;

    public OrderService(OrderRepository orderRepository, ProductClient productClient) {
        this.orderRepository = orderRepository;
        this.productClient = productClient;
    }

    public Order createOrder(Long userId, Long productId, Integer quantity) {
        if (!productClient.productExists(productId)) {
            throw new RuntimeException("Product not found: " + productId);
        }
        Order order = new Order();
        order.setUserId(userId);
        order.setProductId(productId);
        order.setQuantity(quantity);
        order.setStatus("CONFIRMED");
        order.setCreatedAt(LocalDateTime.now());
        Order saved = orderRepository.save(order);
        try {
            // notification failure should not roll back the order
            log.info("Order #{} saved — notification dispatched", saved.getId());
        } catch (Exception e) {
            log.warn("Notification failed for order #{}, will retry later: {}", saved.getId(), e.getMessage());
        }
        return saved;
    }

    public List<Order> getOrdersByUser(Long userId) {
        return orderRepository.findByUserId(userId);
    }
}
""",
        },
    },
    # ── PR 10: N+1 fix (OrderRepository + OrderService) ───────────────────
    {
        "branch": "fix/order-repository-n-plus-one",
        "title": "Fix: resolve N+1 query in OrderRepository.java and add pagination to OrderService.java",
        "body": f"Closes #{issue_numbers[9]}\n\nAdd `@Query` with `JOIN FETCH` to `OrderRepository.java`. Use `Pageable` in `OrderService.java`.",
        "commit_msg": "Fix N+1 query: @Query JOIN FETCH in OrderRepository.java, Pageable in OrderService.java",
        "files": {
            f"{OS}/repository/OrderRepository.java": """\
package com.example.orderservice.repository;

import com.example.orderservice.model.Order;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;

public interface OrderRepository extends JpaRepository<Order, Long> {
    @Query("SELECT o FROM Order o WHERE o.userId = :userId ORDER BY o.createdAt DESC")
    Page<Order> findByUserIdPaged(@Param("userId") Long userId, Pageable pageable);

    List<Order> findByStatus(String status);
}
""",
            f"{OS}/service/OrderService.java": """\
package com.example.orderservice.service;

import com.example.orderservice.client.ProductClient;
import com.example.orderservice.model.Order;
import com.example.orderservice.repository.OrderRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.List;

@Service
public class OrderService {

    private static final Logger log = LoggerFactory.getLogger(OrderService.class);
    private final OrderRepository orderRepository;
    private final ProductClient productClient;

    public OrderService(OrderRepository orderRepository, ProductClient productClient) {
        this.orderRepository = orderRepository;
        this.productClient = productClient;
    }

    public Order createOrder(Long userId, Long productId, Integer quantity) {
        if (!productClient.productExists(productId)) {
            throw new RuntimeException("Product not found: " + productId);
        }
        Order order = new Order();
        order.setUserId(userId);
        order.setProductId(productId);
        order.setQuantity(quantity);
        order.setStatus("CONFIRMED");
        order.setCreatedAt(LocalDateTime.now());
        Order saved = orderRepository.save(order);
        log.info("Order #{} created for user #{}", saved.getId(), userId);
        return saved;
    }

    public List<Order> getOrdersByUser(Long userId) {
        return getOrdersByUser(userId, 0, 20);
    }

    public List<Order> getOrdersByUser(Long userId, int page, int size) {
        Page<Order> result = orderRepository.findByUserIdPaged(
                userId, PageRequest.of(page, size));
        return result.getContent();
    }
}
""",
        },
    },
]

# ── 6. Create branches, PRs, merge ────────────────────────────────────────
print("\nCreating branches, PRs, and merging...")
pr_numbers = []
existing_prs = api("get", f"/repos/{OWNER}/{REPO}/pulls", params={"state": "all", "per_page": 100})
existing_pr_titles = {p["title"]: p["number"] for p in existing_prs}

for i, branch_def in enumerate(BRANCHES):
    branch = branch_def["branch"]
    print(f"\n  [{i+1}/10] {branch}")

    if branch_def["title"] in existing_pr_titles:
        pr_num = existing_pr_titles[branch_def["title"]]
        print(f"    PR #{pr_num} already exists, skipping.")
        pr_numbers.append(pr_num)
        continue

    run("git checkout main", cwd=cwd)
    try:
        run(f"git checkout -b {branch}", cwd=cwd)
    except Exception:
        run(f"git checkout {branch}", cwd=cwd)

    for filepath, content in branch_def["files"].items():
        patch_file(cwd, filepath, content)

    run("git add -A", cwd=cwd)
    msg_file = os.path.join(cwd, ".git", "COMMIT_MSG_TMP")
    with open(msg_file, "w", encoding="utf-8") as f:
        f.write(branch_def["commit_msg"])
    run(f'git commit -F "{msg_file}"', cwd=cwd)
    run(f"git push origin {branch}", cwd=cwd)

    pr = api("post", f"/repos/{OWNER}/{REPO}/pulls", json={
        "title": branch_def["title"],
        "body": branch_def["body"],
        "head": branch,
        "base": "main",
    })
    pr_num = pr["number"]
    pr_numbers.append(pr_num)
    print(f"    PR #{pr_num}: {branch_def['title'][:60]}")
    time.sleep(1)

    try:
        api("put", f"/repos/{OWNER}/{REPO}/pulls/{pr_num}/merge", json={
            "merge_method": "squash",
            "commit_title": branch_def["commit_msg"],
        })
        print(f"    Merged PR #{pr_num}")
    except Exception as e:
        print(f"    Could not merge PR #{pr_num}: {e}")

    run("git checkout main", cwd=cwd)
    run("git pull origin main", cwd=cwd)
    time.sleep(1)

# ── 7. Probe issues ────────────────────────────────────────────────────────
PROBE_ISSUES = [
    {
        "title": "[PROBE-1 FOUND] UserService.java login throws NullPointerException for usernames with special characters",
        "body": (
            "## Description\n"
            "When a user logs in with a username containing special characters (e.g. `alice@domain`), "
            "`UserService.java` throws a NullPointerException inside the repository lookup. "
            "The `findByUsername` call does not guard against edge-case username formats.\n\n"
            "## Steps to reproduce\n"
            "1. `POST /api/users/login` with `{\"username\": \"alice@domain\", \"password\": \"secret\"}`\n"
            "2. NPE thrown inside `UserService.java`\n\n"
            "**Affected files:** `user-service/src/main/java/com/example/userservice/service/UserService.java`\n\n"
            "> **[PROBE]** Should match: issue #1 (UserService NPE), issue #6 (UserService refresh token), "
            "issue #8 (UserService BCrypt) and PRs #11, #16, #18"
        ),
    },
    {
        "title": "[PROBE-2 FOUND] OrderService.java and OrderController.java produce inconsistent order status under concurrent requests",
        "body": (
            "## Description\n"
            "Under concurrent load, `OrderService.java` and `OrderController.java` produce "
            "inconsistent HTTP responses — some requests return 200, others 201, and the "
            "`status` field in the order alternates between `PENDING` and `CONFIRMED`. "
            "There is no optimistic locking on the `Order` entity.\n\n"
            "## Steps to reproduce\n"
            "1. Fire 50 concurrent `POST /api/orders` requests\n"
            "2. Observe mixed 200/201 responses and inconsistent `status` values\n\n"
            "**Affected files:** `order-service/src/main/java/com/example/orderservice/service/OrderService.java`, "
            "`order-service/src/main/java/com/example/orderservice/controller/OrderController.java`\n\n"
            "> **[PROBE]** Should match: issue #3 (OrderService product check), issue #7 (OrderController 201), "
            "issue #9 (OrderService notifications), issue #10 (OrderService N+1) — PRs #13, #17, #19, #20"
        ),
    },
    {
        "title": "[PROBE-3 NOT FOUND] Kubernetes HPA not scaling user-service — deployment.yaml resource limits missing",
        "body": (
            "## Description\n"
            "The Kubernetes Horizontal Pod Autoscaler (HPA) for `user-service` is not triggering "
            "because the `deployment.yaml` does not define CPU/memory resource requests and limits. "
            "Without these, the HPA metrics server cannot compute utilization percentages.\n\n"
            "## Steps to reproduce\n"
            "1. `kubectl apply -f k8s/user-service/deployment.yaml`\n"
            "2. `kubectl get hpa user-service` shows `<unknown>/50%` targets\n"
            "3. Pod count stays at 1 under load\n\n"
            "**Affected files:** `k8s/user-service/deployment.yaml`, `k8s/user-service/hpa.yaml`\n\n"
            "> **[PROBE]** Should NOT match: no Kubernetes files exist in any PR — topic is infra/devops, "
            "no semantic or co-change similarity to any of the 10 closed issues"
        ),
    },
    {
        "title": "[PROBE-4 SPLIT] api-gateway application.yml needs Resilience4J circuit breaker retry policy",
        "body": (
            "## Description\n"
            "The API gateway in `api-gateway/src/main/resources/application.yml` has basic routing "
            "but no retry policy configured in Resilience4J. When `order-service` temporarily fails, "
            "the gateway gives up immediately instead of retrying with exponential backoff.\n\n"
            "## Proposed solution\n"
            "Add `retry` configuration under `resilience4j.retry` in `application.yml` with:\n"
            "- `maxAttempts: 3`\n"
            "- `waitDuration: 500ms`\n"
            "- `enableExponentialBackoff: true`\n\n"
            "**Affected files:** `api-gateway/src/main/resources/application.yml`\n\n"
            "> **[PROBE]** SPLIT: co-change finds PR #14 (only PR touching application.yml), "
            "but vector search should NOT match — retry/backoff policy is a distinct topic from "
            "the fallback routing fix in issue #4"
        ),
    },
]

print("\n\nCreating 4 probe issues...")
existing_all = api("get", f"/repos/{OWNER}/{REPO}/issues", params={"state": "open", "per_page": 100})
existing_probe_titles = {i["title"]: i["number"] for i in existing_all}
probe_numbers = []
for issue in PROBE_ISSUES:
    if issue["title"] in existing_probe_titles:
        num = existing_probe_titles[issue["title"]]
        print(f"  Probe Issue #{num} already exists.")
        probe_numbers.append(num)
    else:
        result = api("post", f"/repos/{OWNER}/{REPO}/issues", json=issue)
        probe_numbers.append(result["number"])
        print(f"  Probe Issue #{result['number']}: {issue['title'][:70]}")
        time.sleep(0.5)

print(f"""
Setup Complete!

  Repo: https://github.com/{OWNER}/{REPO}

  Knowledge base (closed):
    Issues: #{', #'.join(str(n) for n in issue_numbers)}
    PRs:    #{', #'.join(str(n) for n in pr_numbers)}

  Probe issues (open — feed to issue-agent):
    #{probe_numbers[0]} — FOUND      (UserService.java NPE — PRs #11, #16, #18)
    #{probe_numbers[1]} — FOUND      (OrderService + OrderController — PRs #13, #17, #19, #20)
    #{probe_numbers[2]} — NOT FOUND  (k8s deployment.yaml — no match)
    #{probe_numbers[3]} — SPLIT      (api-gateway retry — co-change only, vector miss)
""")
