/**
 * Frontend Logging Service
 * 
 * Enterprise-grade logging with backend synchronization.
 * - Level-based logging (debug, info, warn, error)
 * - Automatic backend sync for warn/error in production
 * - Request correlation via X-Request-ID
 * - Log batching for performance
 */

const LOG_LEVELS = {
  debug: 0,
  info: 1,
  warn: 2,
  error: 3
}

// Configuration
const config = {
  // Minimum level to log to console
  consoleLevel: import.meta.env.DEV ? 'debug' : 'info',
  // Minimum level to send to backend
  backendLevel: 'warn',
  // Backend endpoint
  endpoint: '/api/logs/batch',
  // Batch settings
  batchSize: 10,
  batchIntervalMs: 5000,
  // Enable backend sync
  enableBackendSync: import.meta.env.PROD
}

// State
let logQueue = []
let batchTimer = null
let lastRequestId = null

/**
 * Store the last request ID from API responses.
 * Call this from your axios response interceptor.
 */
export function setRequestId(requestId) {
  lastRequestId = requestId
}

/**
 * Get the current request ID for correlation.
 */
export function getRequestId() {
  return lastRequestId
}

/**
 * Core logging function.
 */
function log(level, message, context = {}) {
  const timestamp = new Date().toISOString()
  const logEntry = {
    level,
    message,
    context,
    timestamp,
    url: window.location.pathname,
    userAgent: navigator.userAgent,
    requestId: lastRequestId
  }

  // Console output
  if (shouldLog(level, config.consoleLevel)) {
    const consoleMethod = level === 'error' ? 'error' 
      : level === 'warn' ? 'warn' 
      : level === 'debug' ? 'debug' 
      : 'log'
    
    console[consoleMethod](
      `[${timestamp}] [${level.toUpperCase()}]`,
      message,
      context
    )
  }

  // Queue for backend sync
  if (config.enableBackendSync && shouldLog(level, config.backendLevel)) {
    queueLog(logEntry)
  }
}

/**
 * Check if log level meets threshold.
 */
function shouldLog(level, threshold) {
  return LOG_LEVELS[level] >= LOG_LEVELS[threshold]
}

/**
 * Queue a log entry for batch sending.
 */
function queueLog(entry) {
  logQueue.push(entry)

  // Send immediately if batch is full
  if (logQueue.length >= config.batchSize) {
    flushLogs()
  } else if (!batchTimer) {
    // Start timer for batch interval
    batchTimer = setTimeout(flushLogs, config.batchIntervalMs)
  }
}

/**
 * Send queued logs to backend.
 */
async function flushLogs() {
  if (batchTimer) {
    clearTimeout(batchTimer)
    batchTimer = null
  }

  if (logQueue.length === 0) return

  const logsToSend = [...logQueue]
  logQueue = []

  try {
    // Use fetch directly to avoid axios interceptors (prevent infinite loops)
    const baseURL = import.meta.env.VITE_API_URL || '/api'
    await fetch(`${baseURL}/logs/batch`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token') || ''}`
      },
      body: JSON.stringify({ logs: logsToSend }),
      credentials: 'include'
    })
  } catch (error) {
    // Log send failed - don't re-queue to prevent infinite loops
    console.error('[Logger] Failed to send logs to backend:', error)
  }
}

/**
 * Logger instance with level methods.
 */
const logger = {
  debug: (message, context) => log('debug', message, context),
  info: (message, context) => log('info', message, context),
  warn: (message, context) => log('warn', message, context),
  error: (message, context) => log('error', message, context),

  /**
   * Log component lifecycle event.
   */
  component: (componentName, event, data = {}) => {
    log('debug', `[${componentName}] ${event}`, data)
  },

  /**
   * Log API request/response.
   */
  api: (method, url, status, durationMs) => {
    const level = status >= 400 ? 'warn' : 'debug'
    log(level, `API ${method} ${url}`, { status, durationMs })
  },

  /**
   * Log user action.
   */
  action: (actionName, data = {}) => {
    log('info', `User action: ${actionName}`, data)
  },

  /**
   * Capture and log an error with stack trace.
   */
  captureError: (error, context = {}) => {
    log('error', error.message || String(error), {
      ...context,
      stack: error.stack,
      name: error.name
    })
  },

  /**
   * Flush pending logs immediately.
   */
  flush: flushLogs,

  /**
   * Update configuration.
   */
  configure: (options) => {
    Object.assign(config, options)
  }
}

// Flush logs before page unload
if (typeof window !== 'undefined') {
  window.addEventListener('beforeunload', flushLogs)
  
  // Global error handler
  window.addEventListener('error', (event) => {
    logger.captureError(event.error || new Error(event.message), {
      filename: event.filename,
      lineno: event.lineno,
      colno: event.colno
    })
  })

  // Unhandled promise rejection handler
  window.addEventListener('unhandledrejection', (event) => {
    logger.captureError(
      event.reason instanceof Error 
        ? event.reason 
        : new Error(String(event.reason)),
      { type: 'unhandledrejection' }
    )
  })
}

export default logger
