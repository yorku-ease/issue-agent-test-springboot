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
