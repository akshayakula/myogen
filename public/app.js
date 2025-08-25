class HandTrackingApp {
    constructor() {
        this.video = document.getElementById('video');
        this.canvas = document.getElementById('canvas');
        this.ctx = this.canvas.getContext('2d');
        this.model = null;
        this.isTracking = false;
        this.socket = io();
        
        this.initializeElements();
        this.setupEventListeners();
        this.setupSocketIO();
        this.loadHandPoseModel();
    }

    initializeElements() {
        // Buttons
        this.startBtn = document.getElementById('start-btn');
        this.stopBtn = document.getElementById('stop-btn');
        this.calibrateBtn = document.getElementById('calibrate-btn');
        
        // Status elements
        this.arduinoStatus = document.getElementById('arduino-status');
        this.modelStatus = document.getElementById('model-status');
        
        // Finger bars
        this.fingerBars = {
            thumb: { bar: document.getElementById('thumb-bar'), value: document.getElementById('thumb-value') },
            index: { bar: document.getElementById('index-bar'), value: document.getElementById('index-value') },
            middle: { bar: document.getElementById('middle-bar'), value: document.getElementById('middle-value') },
            ring: { bar: document.getElementById('ring-bar'), value: document.getElementById('ring-value') },
            pinky: { bar: document.getElementById('pinky-bar'), value: document.getElementById('pinky-value') }
        };
        
        // Servo displays
        this.servoDisplays = [
            document.getElementById('servo-0'),
            document.getElementById('servo-1'),
            document.getElementById('servo-2'),
            document.getElementById('servo-3'),
            document.getElementById('servo-4'),
            document.getElementById('servo-5')
        ];
        
        // Manual control sliders
        this.servoSliders = [];
        for (let i = 0; i < 6; i++) {
            const slider = document.getElementById(`slider-${i}`);
            const valueDisplay = document.getElementById(`slider-${i}-value`);
            this.servoSliders.push({ slider, valueDisplay });
        }
    }

    setupEventListeners() {
        this.startBtn.addEventListener('click', () => this.startTracking());
        this.stopBtn.addEventListener('click', () => this.stopTracking());
        this.calibrateBtn.addEventListener('click', () => this.calibrate());
        
        // Manual servo control
        this.servoSliders.forEach(({ slider, valueDisplay }, index) => {
            slider.addEventListener('input', (e) => {
                const value = parseInt(e.target.value);
                valueDisplay.textContent = value;
                this.socket.emit('set_servo', { servo: index, angle: value });
            });
        });
    }

    setupSocketIO() {
        this.socket.on('connect', () => {
            console.log('Connected to server');
        });

        this.socket.on('status', (data) => {
            this.updateStatus(data);
        });

        this.socket.on('arduino_connected', (data) => {
            this.updateArduinoStatus(true, data.port);
        });

        this.socket.on('arduino_disconnected', () => {
            this.updateArduinoStatus(false);
        });

        this.socket.on('arduino_error', (data) => {
            console.error('Arduino error:', data.error);
            this.updateArduinoStatus(false);
        });

        this.socket.on('servo_updated', (data) => {
            this.updateServoDisplay(data.servo, data.angle);
        });

        this.socket.on('hand_pose', (data) => {
            this.updateFingerExtensions(data.finger_extensions);
            this.updateServoAngles(data.servo_angles);
        });
    }

    async loadHandPoseModel() {
        try {
            this.updateModelStatus('Loading...', false);
            console.log('Loading HandPose model...');
            
            // Load TensorFlow.js backend
            await tf.setBackend('webgl');
            console.log('Using backend:', tf.getBackend());
            
            // Load HandPose model
            this.model = await handpose.load();
            console.log('HandPose model loaded successfully');
            
            this.updateModelStatus('Ready', true);
            this.startBtn.disabled = false;
            
        } catch (error) {
            console.error('Failed to load HandPose model:', error);
            this.updateModelStatus('Error', false);
        }
    }

    async startTracking() {
        if (!this.model) {
            alert('HandPose model not loaded yet');
            return;
        }

        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    width: 640,
                    height: 480,
                    facingMode: 'user'
                }
            });

            this.video.srcObject = stream;
            this.video.addEventListener('loadeddata', () => {
                this.isTracking = true;
                this.startBtn.disabled = true;
                this.stopBtn.disabled = false;
                this.detectHand();
            });

        } catch (error) {
            console.error('Error accessing camera:', error);
            alert('Failed to access camera. Please check permissions.');
        }
    }

    stopTracking() {
        this.isTracking = false;
        this.startBtn.disabled = false;
        this.stopBtn.disabled = true;
        
        if (this.video.srcObject) {
            const tracks = this.video.srcObject.getTracks();
            tracks.forEach(track => track.stop());
            this.video.srcObject = null;
        }
        
        // Clear canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    }

    async detectHand() {
        if (!this.isTracking) return;

        try {
            // Get hand predictions
            const predictions = await this.model.estimateHands(this.video);
            
            // Clear canvas
            this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
            
            if (predictions.length > 0) {
                const hand = predictions[0];
                this.drawHandLandmarks(hand.landmarks);
                this.processHandPose(hand.landmarks);
            }
            
        } catch (error) {
            console.error('Error detecting hand:', error);
        }
        
        // Continue detection
        requestAnimationFrame(() => this.detectHand());
    }

    drawHandLandmarks(landmarks) {
        // Draw landmarks
        landmarks.forEach((landmark, index) => {
            this.ctx.beginPath();
            this.ctx.arc(landmark[0], landmark[1], 3, 0, 2 * Math.PI);
            this.ctx.fillStyle = '#00ff00';
            this.ctx.fill();
        });

        // Draw connections
        const connections = [
            // Thumb
            [0, 1], [1, 2], [2, 3], [3, 4],
            // Index finger
            [0, 5], [5, 6], [6, 7], [7, 8],
            // Middle finger
            [0, 9], [9, 10], [10, 11], [11, 12],
            // Ring finger
            [0, 13], [13, 14], [14, 15], [15, 16],
            // Pinky
            [0, 17], [17, 18], [18, 19], [19, 20],
            // Palm
            [0, 5], [5, 9], [9, 13], [13, 17]
        ];

        connections.forEach(([start, end]) => {
            this.ctx.beginPath();
            this.ctx.moveTo(landmarks[start][0], landmarks[start][1]);
            this.ctx.lineTo(landmarks[end][0], landmarks[end][1]);
            this.ctx.strokeStyle = '#ff0000';
            this.ctx.lineWidth = 2;
            this.ctx.stroke();
        });
    }

    processHandPose(landmarks) {
        // Calculate finger extensions
        const extensions = this.calculateFingerExtensions(landmarks);
        
        // Send to server for servo control
        this.socket.emit('hand_pose', { landmarks, finger_extensions: extensions });
        
        // Update UI
        this.updateFingerExtensions(extensions);
    }

    calculateFingerExtensions(landmarks) {
        const extensions = {};
        
        // Thumb extension (distance from base to tip)
        const thumbBase = landmarks[2];
        const thumbTip = landmarks[4];
        extensions.thumb = this.calculateDistance(thumbBase, thumbTip) / 100;
        
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
            extensions[finger.name] = this.calculateDistance(base, tip) / 100;
        });
        
        return extensions;
    }

    calculateDistance(point1, point2) {
        const dx = point1[0] - point2[0];
        const dy = point1[1] - point2[1];
        return Math.sqrt(dx * dx + dy * dy);
    }

    updateFingerExtensions(extensions) {
        Object.keys(extensions).forEach(finger => {
            const extension = Math.min(1, Math.max(0, extensions[finger]));
            const percentage = Math.round(extension * 100);
            
            this.fingerBars[finger].bar.style.width = `${percentage}%`;
            this.fingerBars[finger].value.textContent = `${percentage}%`;
        });
    }

    updateServoAngles(angles) {
        angles.forEach((angle, index) => {
            this.updateServoDisplay(index, angle);
        });
    }

    updateServoDisplay(servoId, angle) {
        if (this.servoDisplays[servoId]) {
            this.servoDisplays[servoId].textContent = `${angle}°`;
        }
        
        // Update slider if it's not being dragged
        if (this.servoSliders[servoId] && !this.servoSliders[servoId].slider.matches(':active')) {
            this.servoSliders[servoId].slider.value = angle;
            this.servoSliders[servoId].valueDisplay.textContent = angle;
        }
    }

    updateStatus(data) {
        this.updateArduinoStatus(data.arduino_connected);
        this.updateModelStatus(data.model_loaded ? 'Ready' : 'Loading...', data.model_loaded);
    }

    updateArduinoStatus(connected, port = null) {
        const dot = this.arduinoStatus.querySelector('.status-dot');
        const text = this.arduinoStatus.querySelector('.status-text');
        
        if (connected) {
            dot.classList.add('connected');
            text.textContent = `Arduino: Connected${port ? ` (${port})` : ''}`;
        } else {
            dot.classList.remove('connected');
            text.textContent = 'Arduino: Disconnected';
        }
    }

    updateModelStatus(status, ready = false) {
        const dot = this.modelStatus.querySelector('.status-dot');
        const text = this.modelStatus.querySelector('.status-text');
        
        text.textContent = `Model: ${status}`;
        
        if (ready) {
            dot.classList.add('connected');
        } else {
            dot.classList.remove('connected');
        }
    }

    calibrate() {
        // Reset all servos to center position
        const centerAngles = [90, 90, 90, 90, 90, 90];
        this.socket.emit('set_servos', { angles: centerAngles });
        
        // Update UI
        centerAngles.forEach((angle, index) => {
            this.updateServoDisplay(index, angle);
            if (this.servoSliders[index]) {
                this.servoSliders[index].slider.value = angle;
                this.servoSliders[index].valueDisplay.textContent = angle;
            }
        });
        
        console.log('Calibration complete - all servos set to center position');
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new HandTrackingApp();
});
