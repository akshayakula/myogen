#!/usr/bin/env node

const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const path = require('path');

class HandControllerDemo {
    constructor() {
        this.isConnected = false;
        this.servoAngles = [90, 90, 90, 90, 90, 90];
        this.app = express();
        this.server = http.createServer(this.app);
        this.io = socketIo(this.server);
        
        this.setupWebServer();
        this.setupSocketIO();
        this.startDemo();
    }

    setupWebServer() {
        // Serve static files
        this.app.use(express.static(path.join(__dirname, 'public')));
        
        // API routes
        this.app.get('/api/status', (req, res) => {
            res.json({
                arduino_connected: this.isConnected,
                model_loaded: true,
                servo_angles: this.servoAngles
            });
        });

        this.app.get('/api/servo/:id/:angle', (req, res) => {
            const servoId = parseInt(req.params.id);
            const angle = parseInt(req.params.angle);
            
            if (servoId >= 0 && servoId < 6 && angle >= 0 && angle <= 180) {
                this.setServoAngle(servoId, angle);
                res.json({ success: true, servo: servoId, angle: angle });
            } else {
                res.status(400).json({ error: 'Invalid servo ID or angle' });
            }
        });

        this.app.post('/api/servos', (req, res) => {
            const angles = req.body.angles;
            if (Array.isArray(angles) && angles.length === 6) {
                this.setServoAngles(angles);
                res.json({ success: true, angles: angles });
            } else {
                res.status(400).json({ error: 'Invalid angles array' });
            }
        });
    }

    setupSocketIO() {
        this.io.on('connection', (socket) => {
            console.log('🌐 Client connected');
            
            socket.emit('status', {
                arduino_connected: this.isConnected,
                model_loaded: true,
                servo_angles: this.servoAngles
            });

            socket.on('disconnect', () => {
                console.log('🌐 Client disconnected');
            });

            socket.on('set_servo', (data) => {
                this.setServoAngle(data.servo, data.angle);
            });

            socket.on('set_servos', (data) => {
                this.setServoAngles(data.angles);
            });

            socket.on('hand_pose', (data) => {
                this.processHandPose(data.landmarks);
            });
        });
    }

    setServoAngle(servoId, angle) {
        // Clamp angle to valid range
        angle = Math.max(0, Math.min(180, angle));
        this.servoAngles[servoId] = angle;
        
        console.log(`🎯 Servo ${servoId}: ${angle}°`);
        this.io.emit('servo_updated', { servo: servoId, angle: angle });
    }

    setServoAngles(angles) {
        angles.forEach((angle, index) => {
            this.setServoAngle(index, angle);
        });
    }

    processHandPose(landmarks) {
        if (!landmarks || landmarks.length === 0) {
            return;
        }

        // Calculate finger extensions (0.0 = closed, 1.0 = extended)
        const fingerExtensions = this.calculateFingerExtensions(landmarks);
        
        // Map finger extensions to servo angles
        const servoAngles = this.mapExtensionsToServoAngles(fingerExtensions);
        
        // Update servos
        this.setServoAngles(servoAngles);
        
        // Send data to web interface
        this.io.emit('hand_pose', {
            landmarks: landmarks,
            finger_extensions: fingerExtensions,
            servo_angles: servoAngles
        });
    }

    calculateFingerExtensions(landmarks) {
        // HandPose landmarks: 21 points
        // Thumb: 0-4, Index: 5-8, Middle: 9-12, Ring: 13-16, Pinky: 17-20
        
        const extensions = {};
        
        // Thumb extension (distance from base to tip)
        const thumbBase = landmarks[2];
        const thumbTip = landmarks[4];
        extensions.thumb = this.calculateDistance(thumbBase, thumbTip) / 100; // Normalize
        
        // Other fingers (distance from MCP to tip)
        const fingerIndices = [
            { name: 'index', base: 5, tip: 8 },
            { name: 'middle', base: 9, tip: 12 },
            { name: 'ring', base: 13, tip: 16 },
            { name: 'pinky', base: 17, tip: 20 }
        ];
        
        fingerIndices.forEach(finger => {
            const base = landmarks[finger.base];
            const tip = landmarks[finger.tip];
            extensions[finger.name] = this.calculateDistance(base, tip) / 100; // Normalize
        });
        
        return extensions;
    }

    calculateDistance(point1, point2) {
        const dx = point1[0] - point2[0];
        const dy = point1[1] - point2[1];
        return Math.sqrt(dx * dx + dy * dy);
    }

    mapExtensionsToServoAngles(extensions) {
        // Map finger extensions (0.0-1.0) to servo angles (0-180)
        return [
            Math.round(extensions.thumb * 180),      // Servo 0: Thumb
            Math.round(extensions.index * 180),      // Servo 1: Index
            Math.round(extensions.middle * 180),     // Servo 2: Middle
            Math.round(extensions.ring * 180),       // Servo 3: Ring
            Math.round(extensions.pinky * 180),      // Servo 4: Pinky
            90  // Servo 5: Wrist (fixed for now)
        ];
    }

    startDemo() {
        console.log('🎭 Starting Hand Controller Demo...');
        console.log('📱 Open http://localhost:3000 in your browser');
        console.log('🔌 Arduino connection is simulated for demo purposes');
        
        // Simulate Arduino connection after 2 seconds
        setTimeout(() => {
            this.isConnected = true;
            console.log('✅ Arduino connection simulated');
            this.io.emit('arduino_connected', { port: 'DEMO_MODE' });
        }, 2000);
    }

    startServer(port = 3000) {
        this.server.listen(port, () => {
            console.log(`🌐 Demo server running on http://localhost:${port}`);
            console.log('📱 Open the web interface to start hand tracking');
        });
    }
}

// Main execution
async function main() {
    const controller = new HandControllerDemo();
    controller.startServer();
}

if (require.main === module) {
    main();
}

module.exports = HandControllerDemo;
