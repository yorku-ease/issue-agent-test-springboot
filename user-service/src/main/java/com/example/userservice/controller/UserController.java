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
