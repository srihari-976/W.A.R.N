import { EventEmitter } from 'events';

class WebSocketService {
  constructor() {
    this.ws = null;
    this.eventEmitter = new EventEmitter();
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectTimeout = 3000;
  }

  connect() {
    try {
      this.ws = new WebSocket('ws://127.0.0.1:5000/ws');

      this.ws.onopen = () => {
        console.log('WebSocket Connected');
        this.reconnectAttempts = 0;
        this.eventEmitter.emit('connected');
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.eventEmitter.emit('message', data);
          
          // Emit specific events based on data type
          if (data.type === 'process_termination') {
            this.eventEmitter.emit('process_termination', data);
          } else if (data.type === 'threat_detected') {
            this.eventEmitter.emit('threat_detected', data);
          } else if (data.type === 'system_update') {
            this.eventEmitter.emit('system_update', data);
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      this.ws.onclose = () => {
        console.log('WebSocket Disconnected');
        this.eventEmitter.emit('disconnected');
        this.attemptReconnect();
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket Error:', error);
        this.eventEmitter.emit('error', error);
      };
    } catch (error) {
      console.error('Error creating WebSocket:', error);
      this.attemptReconnect();
    }
  }

  attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
      setTimeout(() => this.connect(), this.reconnectTimeout);
    }
  }

  on(event, callback) {
    this.eventEmitter.on(event, callback);
  }

  off(event, callback) {
    this.eventEmitter.off(event, callback);
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
    }
  }
}

const websocketService = new WebSocketService();
export default websocketService; 