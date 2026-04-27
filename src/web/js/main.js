/* ═══════════════════════════════════════════════════════════════════
   JARVIS ISL TRANSLATION SYSTEM - MAIN JAVASCRIPT
   Handles UI interactions, Eel communication, and metrics tracking
   ═══════════════════════════════════════════════════════════════════ */

// ─────────────────────────────────────────────────────────────────
// 1. DOM REFERENCES
// ─────────────────────────────────────────────────────────────────
const messagesContainer = document.getElementById('messages');
const userInput = document.getElementById('userInput');
const sendButton = document.getElementById('userInputButton');
const voiceInterface = document.getElementById('voiceInterface');
const textInterface = document.getElementById('textInterface');
const typingIndicator = document.getElementById('typingIndicator');
const subtitleStrip = document.getElementById('subtitleStrip');
const subtitleText = document.getElementById('subtitleText');
const metricsPanel = document.getElementById('metricsPanel');
const metricsToggle = document.getElementById('metricsToggle');
const metricsClose = document.getElementById('metricsClose');
const backendToggle = document.getElementById('backendToggle');

// ─────────────────────────────────────────────────────────────────
// 2. STATE MANAGEMENT
// ─────────────────────────────────────────────────────────────────
const state = {
  messageCount: 0,
  latencies: [],
  currentBackend: 'GROQ',
  isTyping: false,
  micActive: true
};

// ─────────────────────────────────────────────────────────────────
// 3. AUTO-SCROLL FUNCTIONALITY
// ─────────────────────────────────────────────────────────────────
function scrollToBottom() {
  requestAnimationFrame(() => {
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  });
}

// Observer for auto-scroll on new messages
const scrollObserver = new MutationObserver(() => {
  scrollToBottom();
});

scrollObserver.observe(messagesContainer, {
  childList: true,
  subtree: true
});

// ─────────────────────────────────────────────────────────────────
// 4. EEL EXPOSED FUNCTIONS (Python → JavaScript)
// ─────────────────────────────────────────────────────────────────

/**
 * Add user message to chat
 * Called from Python: app.ChatBot.addUserMsg(msg)
 */
eel.expose(addUserMsg);
function addUserMsg(msg) {
  const messageDiv = document.createElement('div');
  messageDiv.className = 'message to';
  messageDiv.textContent = msg;
  messagesContainer.appendChild(messageDiv);
  
  state.messageCount++;
  updateMetrics();
  scrollToBottom();
}

/**
 * Add assistant message to chat
 * Called from Python: app.ChatBot.addAppMsg(msg)
 */
eel.expose(addAppMsg);
function addAppMsg(msg, metadata = null) {
  hideThinking();
  
  const messageDiv = document.createElement('div');
  messageDiv.className = 'message from';
  
  // Parse HTML content (for <b>, <br>, etc.)
  messageDiv.innerHTML = msg;
  
  // Add metadata badges if provided (LLM source, latency)
  if (metadata) {
    const metaDiv = document.createElement('div');
    metaDiv.className = 'message-meta';
    
    if (metadata.source) {
      const sourceBadge = document.createElement('span');
      sourceBadge.className = `meta-badge ${metadata.source.toLowerCase()}`;
      sourceBadge.textContent = metadata.source.toUpperCase();
      metaDiv.appendChild(sourceBadge);
    }
    
    if (metadata.latency) {
      const latencyBadge = document.createElement('span');
      latencyBadge.className = 'meta-badge';
      latencyBadge.textContent = `${metadata.latency}ms`;
      metaDiv.appendChild(latencyBadge);
      
      // Track latency
      state.latencies.push(metadata.latency);
      updateMetrics();
    }
    
    messageDiv.appendChild(metaDiv);
  }
  
  messagesContainer.appendChild(messageDiv);
  state.messageCount++;
  updateMetrics();
  scrollToBottom();
}

/**
 * Toggle text input visibility (fallback mode)
 * Called from Python: app.eel.toggleInput(True/False)
 */
eel.expose(toggleInput);
function toggleInput(show) {
  if (show) {
    voiceInterface.style.display = 'none';
    textInterface.style.display = 'flex';
    userInput.focus();
  } else {
    textInterface.style.display = 'none';
    voiceInterface.style.display = 'flex';
  }
}

/**
 * Show "thinking" indicator (LLM processing)
 * Called from Python: eel.showThinking()
 */
eel.expose(showThinking);
function showThinking() {
  if (!state.isTyping) {
    typingIndicator.style.display = 'flex';
    state.isTyping = true;
    scrollToBottom();
  }
}

/**
 * Hide "thinking" indicator
 * Called from Python: eel.hideThinking()
 */
eel.expose(hideThinking);
function hideThinking() {
  if (state.isTyping) {
    typingIndicator.style.display = 'none';
    state.isTyping = false;
  }
}

/**
 * Set microphone state (animate voice interface)
 * Called from Python: eel.setMicState("on" | "off")
 */
eel.expose(setMicState);
function setMicState(status) {
  state.micActive = (status === "on");
  const waveBars = document.querySelectorAll('.wave-bar');
  
  if (status === "on") {
    waveBars.forEach(bar => bar.style.animationPlayState = 'running');
  } else {
    waveBars.forEach(bar => bar.style.animationPlayState = 'paused');
  }
}

/**
 * Show live subtitle strip (ISL translation in progress)
 * Called from Python: eel.showSubtitle(text)
 */
eel.expose(showSubtitle);
function showSubtitle(text) {
  if (text && text.trim() !== '') {
    subtitleText.textContent = text;
    subtitleStrip.style.display = 'block';
  }
}

/**
 * Hide subtitle strip
 * Called from Python: eel.hideSubtitle()
 */
eel.expose(hideSubtitle);
function hideSubtitle() {
  subtitleStrip.style.display = 'none';
  subtitleText.textContent = '';
}

// ─────────────────────────────────────────────────────────────────
// 5. USER INPUT HANDLING
// ─────────────────────────────────────────────────────────────────
function sendMessage() {
  const msg = userInput.value.trim();
  
  if (msg.length === 0) return;
  
  // Add to UI immediately
  addUserMsg(msg);
  
  // Send to Python backend
  eel.getUserInput(msg);
  
  // Clear input
  userInput.value = '';
  userInput.focus();
}

// Send button click
sendButton.addEventListener('click', sendMessage);

// Enter key press
userInput.addEventListener('keypress', (e) => {
  if (e.key === 'Enter') {
    sendMessage();
  }
});

// ─────────────────────────────────────────────────────────────────
// 6. BACKEND SWITCHING
// ─────────────────────────────────────────────────────────────────
function switchBackend() {
  const selectedBackend = backendToggle.value;
  state.currentBackend = selectedBackend;
  
  // Call Python endpoint to update backend
  eel.set_llm_backend(selectedBackend);
  
  // Update metrics panel
  updateMetrics();
  
  // Visual feedback
  const systemMsg = document.createElement('div');
  systemMsg.className = 'message from';
  systemMsg.innerHTML = `<em style="opacity: 0.7;">Switched to ${selectedBackend === 'MLX' ? '🧠 Local MLX' : '⚡ Groq Cloud'}</em>`;
  messagesContainer.appendChild(systemMsg);
  scrollToBottom();
}

// ─────────────────────────────────────────────────────────────────
// 7. METRICS PANEL
// ─────────────────────────────────────────────────────────────────
function updateMetrics() {
  // Update message count
  document.getElementById('metricMessages').textContent = state.messageCount;
  
  // Update backend
  const backendName = state.currentBackend === 'MLX' ? '🧠 MLX' : '⚡ Groq';
  document.getElementById('metricBackend').textContent = backendName;
  
  // Update average latency
  if (state.latencies.length > 0) {
    const avgLatency = Math.round(
      state.latencies.reduce((a, b) => a + b, 0) / state.latencies.length
    );
    document.getElementById('metricLatency').textContent = `${avgLatency}ms`;
  }
  
  // Update mode (hardcoded for now, can be dynamic)
  document.getElementById('metricMode').textContent = 'ISL';
}

// Toggle metrics panel
metricsToggle.addEventListener('click', () => {
  metricsPanel.style.display = 
    metricsPanel.style.display === 'none' ? 'block' : 'none';
});

// Close metrics panel
metricsClose.addEventListener('click', () => {
  metricsPanel.style.display = 'none';
});

// Close on outside click
document.addEventListener('click', (e) => {
  if (metricsPanel.style.display === 'block' && 
      !metricsPanel.contains(e.target) && 
      !metricsToggle.contains(e.target)) {
    metricsPanel.style.display = 'none';
  }
});

// ─────────────────────────────────────────────────────────────────
// 8. KEYBOARD SHORTCUTS
// ─────────────────────────────────────────────────────────────────
document.addEventListener('keydown', (e) => {
  // Ctrl/Cmd + K: Toggle metrics
  if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
    e.preventDefault();
    metricsToggle.click();
  }
  
  // Escape: Close metrics panel
  if (e.key === 'Escape' && metricsPanel.style.display === 'block') {
    metricsPanel.style.display = 'none';
  }
});

// ─────────────────────────────────────────────────────────────────
// 9. INITIAL SETUP
// ─────────────────────────────────────────────────────────────────
window.addEventListener('DOMContentLoaded', () => {
  console.log('🚀 JARVIS UI Loaded');
  
  // Set initial backend state
  state.currentBackend = backendToggle.value;
  updateMetrics();
  
  // Focus input if visible
  if (textInterface.style.display === 'flex') {
    userInput.focus();
  }
  
  // Welcome message (optional)
  setTimeout(() => {
    scrollToBottom();
  }, 100);
});

// ─────────────────────────────────────────────────────────────────
// 10. UTILITY FUNCTIONS
// ─────────────────────────────────────────────────────────────────

/**
 * Format timestamp
 */
function getTimestamp() {
  const now = new Date();
  return now.toLocaleTimeString('en-US', { 
    hour: '2-digit', 
    minute: '2-digit' 
  });
}

/**
 * Sanitize HTML to prevent XSS (basic)
 */
function sanitizeHTML(str) {
  const temp = document.createElement('div');
  temp.textContent = str;
  return temp.innerHTML;
}

/**
 * Show notification (future enhancement)
 */
function showNotification(message, type = 'info') {
  // Could add toast notifications here
  console.log(`[${type.toUpperCase()}] ${message}`);
}

// ─────────────────────────────────────────────────────────────────
// 11. DEBUG HELPERS (Remove in production)
// ─────────────────────────────────────────────────────────────────
window.DEBUG = {
  addTestMessage: (type = 'user') => {
    if (type === 'user') {
      addUserMsg('This is a test user message');
    } else {
      addAppMsg('This is a test system response with <b>bold text</b>.', {
        source: 'mlx',
        latency: 842
      });
    }
  },
  
  showThinking: () => showThinking(),
  hideThinking: () => hideThinking(),
  
  showSubtitle: (text) => showSubtitle(text || 'HELLO WORLD'),
  hideSubtitle: () => hideSubtitle(),
  
  getState: () => state
};

console.log('💡 Debug helpers available: window.DEBUG');