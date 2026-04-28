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
