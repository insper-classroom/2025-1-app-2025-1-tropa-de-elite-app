// Use dynamic import to handle server vs client environments
let EventSource: any;
if (typeof window !== 'undefined') {
  // Client-side: use the native EventSource
  EventSource = window.EventSource;
} else {
  // Server-side: will not be used, but prevents import errors
  EventSource = null;
}

export interface LogMessage {
  timestamp: string;
  level: string;
  message: string;
}

type LogCallback = (log: LogMessage) => void;

export class LogStream {
  private eventSource: EventSource | null = null;
  private callbacks: LogCallback[] = [];
  
  constructor(private url: string = '/api/logs/stream') {}
  
  public subscribe(callback: LogCallback): () => void {
    this.callbacks.push(callback);
    
    if (!this.eventSource) {
      this.connect();
    }
    
    // Return unsubscribe function
    return () => {
      this.callbacks = this.callbacks.filter(cb => cb !== callback);
      if (this.callbacks.length === 0) {
        this.disconnect();
      }
    };
  }
  
  private connect() {
    // Skip connection if we're not in browser environment or EventSource is not available
    if (typeof window === 'undefined' || !EventSource) {
      console.warn('EventSource not available in this environment');
      return;
    }
    
    try {
      this.eventSource = new EventSource(this.url);
      
      this.eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as LogMessage;
          this.callbacks.forEach(callback => callback(data));
        } catch (error) {
          console.error('Error parsing log event:', error);
        }
      };
      
      this.eventSource.onerror = () => {
        console.error('LogStream connection error, reconnecting...');
        this.disconnect();
        setTimeout(() => this.connect(), 5000);
      };
    } catch (error) {
      console.error('Failed to connect to log stream:', error);
    }
  }
  
  private disconnect() {
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }
  }
}

// Singleton instance
export const logStream = new LogStream();
