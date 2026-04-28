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
