#!/usr/bin/env node

const { SerialPort } = require('serialport');

class ArduinoTester {
    constructor() {
        this.port = null;
        this.isConnected = false;
    }

    async connect() {
        try {
            // List available ports
            const ports = await SerialPort.list();
            console.log('Available ports:');
            ports.forEach(port => {
                console.log(`  - ${port.path} (${port.manufacturer || 'Unknown'})`);
            });

            // Find Arduino
            const arduinoPort = ports.find(port => 
                port.manufacturer && 
                (port.manufacturer.includes('Arduino') || 
                 port.manufacturer.includes('CH340') ||
                 port.manufacturer.includes('FTDI'))
            );

            if (!arduinoPort) {
                console.log('❌ Arduino not found. Please connect Arduino and try again.');
                return false;
            }

            console.log(`🔌 Connecting to Arduino at ${arduinoPort.path}...`);
            
            this.port = new SerialPort({
                path: arduinoPort.path,
                baudRate: 115200,
                autoOpen: false
            });

            return new Promise((resolve, reject) => {
                this.port.on('open', () => {
                    console.log('✅ Arduino connected successfully');
                    this.isConnected = true;
                    resolve(true);
                });

                this.port.on('data', (data) => {
                    console.log('📥 Arduino data:', data.toString().trim());
                });

                this.port.on('error', (error) => {
                    console.error('❌ Arduino error:', error);
                    this.isConnected = false;
                    reject(error);
                });

                this.port.open();
            });

        } catch (error) {
            console.error('❌ Failed to connect to Arduino:', error);
            return false;
        }
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

    setServo(servoId, angle) {
        if (!this.isConnected) {
            console.log('⚠️  Arduino not connected');
            return;
        }

        const command = this.createServoCommand(servoId, angle);
        this.port.write(command);
        console.log(`🎯 Servo ${servoId}: ${angle}°`);
    }

    async runTest() {
        console.log('🧪 Starting Arduino communication test...\n');

        const connected = await this.connect();
        if (!connected) {
            return;
        }

        // Wait a moment for Arduino to initialize
        await new Promise(resolve => setTimeout(resolve, 2000));

        console.log('\n🎮 Testing servo movements...\n');

        // Test each servo
        for (let servo = 0; servo < 6; servo++) {
            console.log(`Testing Servo ${servo}:`);
            
            // Move to center
            this.setServo(servo, 90);
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            // Move to min
            this.setServo(servo, 0);
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            // Move to max
            this.setServo(servo, 180);
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            // Back to center
            this.setServo(servo, 90);
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            console.log(`✅ Servo ${servo} test complete\n`);
        }

        console.log('🎉 All tests completed!');
        
        // Keep connection open for manual testing
        console.log('\n💡 You can now manually test servos. Press Ctrl+C to exit.');
        
        // Set up manual control
        process.stdin.setRawMode(true);
        process.stdin.resume();
        process.stdin.setEncoding('utf8');
        
        let currentServo = 0;
        let currentAngle = 90;
        
        console.log(`\n🎮 Manual Control Mode:`);
        console.log(`   Servo: ${currentServo} | Angle: ${currentAngle}°`);
        console.log(`   Use arrow keys to change servo/angle`);
        console.log(`   Press 'q' to quit`);
        
        process.stdin.on('data', (key) => {
            if (key === 'q') {
                console.log('\n👋 Goodbye!');
                process.exit(0);
            }
            
            switch(key) {
                case '\u001b[A': // Up arrow
                    currentAngle = Math.min(180, currentAngle + 10);
                    break;
                case '\u001b[B': // Down arrow
                    currentAngle = Math.max(0, currentAngle - 10);
                    break;
                case '\u001b[C': // Right arrow
                    currentServo = (currentServo + 1) % 6;
                    break;
                case '\u001b[D': // Left arrow
                    currentServo = (currentServo - 1 + 6) % 6;
                    break;
            }
            
            this.setServo(currentServo, currentAngle);
            console.log(`   Servo: ${currentServo} | Angle: ${currentAngle}°`);
        });
    }

    disconnect() {
        if (this.port && this.isConnected) {
            this.port.close();
            console.log('🔌 Arduino disconnected');
        }
    }
}

// Main execution
async function main() {
    const tester = new ArduinoTester();
    
    // Handle graceful shutdown
    process.on('SIGINT', () => {
        console.log('\n🛑 Shutting down...');
        tester.disconnect();
        process.exit(0);
    });
    
    try {
        await tester.runTest();
    } catch (error) {
        console.error('❌ Test failed:', error);
        tester.disconnect();
        process.exit(1);
    }
}

if (require.main === module) {
    main();
}

module.exports = ArduinoTester;
