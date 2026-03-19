// Simple event bus for cross-component communication
const listeners = {};

const eventBus = {
  on(event, callback) {
    if (!listeners[event]) listeners[event] = [];
    listeners[event].push(callback);
    return () => {
      listeners[event] = listeners[event].filter((cb) => cb !== callback);
    };
  },
  emit(event, data) {
    (listeners[event] || []).forEach((cb) => cb(data));
  },
};

export default eventBus;
