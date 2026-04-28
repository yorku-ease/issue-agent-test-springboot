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
