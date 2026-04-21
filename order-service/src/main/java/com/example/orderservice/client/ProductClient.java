package com.example.orderservice.client;

import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;

@Component
public class ProductClient {

    private final RestTemplate restTemplate;
    private static final String PRODUCT_SERVICE_URL = "http://product-service:8083";

    public ProductClient(RestTemplate restTemplate) {
        this.restTemplate = restTemplate;
    }

    // BUG: returns false on any exception — hides network errors from caller
    public boolean productExists(Long productId) {
        try {
            restTemplate.getForObject(PRODUCT_SERVICE_URL + "/api/products/" + productId, Object.class);
            return true;
        } catch (Exception e) {
            return false;
        }
    }

    public Integer getStock(Long productId) {
        try {
            return restTemplate.getForObject(
                    PRODUCT_SERVICE_URL + "/api/products/" + productId + "/stock", Integer.class);
        } catch (Exception e) {
            return null;
        }
    }
}
