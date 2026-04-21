package com.example.userservice.controller;

import com.example.userservice.model.User;
import com.example.userservice.service.UserService;
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

    // BUG: no @Valid or DTO — accepts any payload without validation
    @PostMapping("/register")
    public ResponseEntity<?> register(@RequestBody Map<String, String> request) {
        User user = userService.register(
                request.get("username"),
                request.get("password"),
                request.get("email")
        );
        return ResponseEntity.ok(Map.of("id", user.getId(), "username", user.getUsername()));
    }

    @GetMapping("/{username}")
    public ResponseEntity<?> getUser(@PathVariable String username) {
        User user = userService.findByUsername(username);
        return ResponseEntity.ok(Map.of("username", user.getUsername(), "email", user.getEmail()));
    }
}
