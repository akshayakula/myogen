#!/usr/bin/env node

const { SerialPort } = require('serialport');
const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const path = require('path');

class HandController {
    constructor() {
        this.port = null;
        this.isConnected = false;
        this.servoAngles = [90, 90, 90, 90, 90, 90]; // Default angles for 6 servos
        this.app = express();
        this.server = http.createServer(this.app);
        this.io = socketIo(this.server);
        
        this.setupWebServer();
        this.setupSocketIO();
    }

    async initialize() {
        console.log('🚀 Initializing Hand Controller...');
        
        // Initialize Arduino connection
        await this.connectToArduino();
    }

    async connectToArduino() {
        try {
            // Auto-detect Arduino port
            const ports = await SerialPort.list();
            const arduinoPort = ports.find(port => 
                port.manufacturer && 
                (port.manufacturer.includes('Arduino') || 
                 port.manufacturer.includes('CH340') ||
                 port.manufacturer.includes('FTDI'))
            );

            if (!arduinoPort) {
                console.log('⚠️  Arduino not found. Available ports:');
                ports.forEach(port => {
                    console.log(`   - ${port.path} (${port.manufacturer || 'Unknown'})`);
                });
                console.log('🔌 Please connect Arduino and restart');
                return;
            }

            console.log(`🔌 Connecting to Arduino at ${arduinoPort.path}...`);
            
            this.port = new SerialPort({
                path: arduinoPort.path,
                baudRate: 115200,
                autoOpen: false
            });

            this.port.on('open', () => {
                console.log('✅ Arduino connected successfully');
                this.isConnected = true;
                this.io.emit('arduino_connected', { port: arduinoPort.path });
            });

            this.port.on('data', (data) => {
                console.log('📥 Arduino data:', data.toString());
                this.io.emit('arduino_data', { data: data.toString() });
            });

            this.port.on('error', (error) => {
                console.error('❌ Arduino error:', error);
                this.isConnected = false;
                this.io.emit('arduino_error', { error: error.message });
            });

            this.port.on('close', () => {
                console.log('🔌 Arduino disconnected');
                this.isConnected = false;
                this.io.emit('arduino_disconnected');
            });

            this.port.open();

        } catch (error) {
            console.error('❌ Failed to connect to Arduino:', error);
        }
    }

    setupWebServer() {
        // Serve static files
        this.app.use(express.static(path.join(__dirname, 'public')));
        
        // API routes
        this.app.get('/api/status', (req, res) => {
            res.json({
                arduino_connected: this.isConnected,
                model_loaded: true, // Model is loaded in browser
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
                model_loaded: true, // Model is loaded in browser
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
        });
    }

    setServoAngle(servoId, angle) {
        if (!this.isConnected) {
            console.log('⚠️  Arduino not connected');
            return;
        }

        // Clamp angle to valid range
        angle = Math.max(0, Math.min(180, angle));
        this.servoAngles[servoId] = angle;

        // Send servo command to Arduino
        const command = this.createServoCommand(servoId, angle);
        this.port.write(command);
        
        console.log(`🎯 Servo ${servoId}: ${angle}°`);
        this.io.emit('servo_updated', { servo: servoId, angle: angle });
    }

    setServoAngles(angles) {
        if (!this.isConnected) {
            console.log('⚠️  Arduino not connected');
            return;
        }

        angles.forEach((angle, index) => {
            this.setServoAngle(index, angle);
        });
    }

    createServoCommand(servoId, angle) {
        // Arduino serial protocol: 0xAA 0x77 [FUNC_SET_SERVO] [Length] [ServoID] [Angle] [Checksum]
        const FUNC_SET_SERVO = 0x01;
        const data = [servoId, angle];
        const checksum = this.calculateChecksum([FUNC_SET_SERVO, data.length, ...data]);
        
        return Buffer.from([0xAA, 0x77, FUNC_SET_SERVO, data.length, ...data, checksum]);
    }

    calculateChecksum(data) {
        return data.reduce((sum, byte) => sum ^ byte, 0);
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

    startServer(port = 3000) {
        this.server.listen(port, () => {
            console.log(`🌐 Web server running on http://localhost:${port}`);
            console.log('📱 Open the web interface to start hand tracking');
        });
    }
}

// Main execution
async function main() {
    const controller = new HandController();
    
    try {
        await controller.initialize();
        controller.startServer();
    } catch (error) {
        console.error('❌ Failed to initialize controller:', error);
        process.exit(1);
    }
}

if (require.main === module) {
    main();
}

module.exports = HandController;
