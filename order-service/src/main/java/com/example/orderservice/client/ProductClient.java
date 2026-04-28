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
