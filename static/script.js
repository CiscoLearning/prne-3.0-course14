const socket = io();
let commandHistory = [];
let currentHistoryPos = -1;
let commandInProgress = false;
let isConnected = false;
let isConnecting = false;

function toggleConnection() {
  if (isConnecting) return;
  if (!isConnected) {
    const deviceSelect = document.getElementById('device-select');
    const deviceId = deviceSelect.value;
    if (!deviceId) { alert('Please select a device to connect.'); return; }
    deviceSelect.disabled = true;
    const connectBtn = document.getElementById('connect-btn');
    connectBtn.textContent = 'Connecting...';
    connectBtn.disabled = true;
    isConnecting = true;
    socket.emit('connect_to_device', { device_id: deviceId });
    setTimeout(() => {
      if (isConnecting && !isConnected) {
        alert('Failed to connect. Please try again.');
        connectBtn.textContent = 'Connect';
        connectBtn.disabled = false;
        deviceSelect.disabled = false;
        isConnecting = false;
      }
    }, 10000);
  } else {
    socket.emit('disconnect_from_device');
    isConnected = false;
    isConnecting = false;
    const deviceSelect = document.getElementById('device-select');
    deviceSelect.disabled = false;
    const connectBtn = document.getElementById('connect-btn');
    connectBtn.textContent = 'Connect';
    connectBtn.disabled = false;
    document.getElementById('command-line').style.display = 'none';
    const commandInput = document.getElementById('command-input');
    commandInput.value = '';
    commandInput.disabled = true;
  }
}

socket.on('console_output', function(data) {
  const consoleDiv = document.getElementById('console');
  const commandLine = document.getElementById('command-line');
  const newLine = document.createElement('div');
  newLine.className = 'line';
  newLine.innerHTML = data.data.replace(/\n/g, '<br>');
  consoleDiv.insertBefore(newLine, commandLine);
  consoleDiv.scrollTop = consoleDiv.scrollHeight;

  if (!isConnected && data.data.includes("Connected to")) {
    isConnected = true;
    isConnecting = false;
    const connectBtn = document.getElementById('connect-btn');
    connectBtn.textContent = 'Disconnect';
    connectBtn.disabled = false;
    document.getElementById('command-line').style.display = 'flex';
    const commandInput = document.getElementById('command-input');
    commandInput.disabled = false;
    commandInput.focus();
    commandInProgress = false;
  }
  if (commandInProgress && /[#>]\s*$/.test(data.data)) {
    commandInProgress = false;
    const commandInput = document.getElementById('command-input');
    commandInput.disabled = false;
    commandInput.focus();
  }
});

const commandInput = document.getElementById('command-input');
commandInput.addEventListener('keydown', function(e) {
  if (e.key === 'Enter') {
    if (commandInProgress) { e.preventDefault(); return; }
    const command = commandInput.value.trim();
    if (command) {
      socket.emit('command', { command: command });
      commandHistory.push(command);
      currentHistoryPos = commandHistory.length;
      const consoleDiv = document.getElementById('console');
      const commandLine = document.getElementById('command-line');
      const newLine = document.createElement('div');
      newLine.className = 'line';
      newLine.textContent = '> ' + command;
      consoleDiv.insertBefore(newLine, commandLine);
      commandInput.value = '';
      commandInProgress = true;
      commandInput.disabled = true;
    }
    e.preventDefault();
  } else if (e.key === 'ArrowUp') {
    e.preventDefault();
    if (currentHistoryPos > 0) {
      currentHistoryPos--;
      commandInput.value = commandHistory[currentHistoryPos];
    }
  } else if (e.key === 'ArrowDown') {
    e.preventDefault();
    if (currentHistoryPos < commandHistory.length - 1) {
      currentHistoryPos++;
      commandInput.value = commandHistory[currentHistoryPos];
    } else {
      currentHistoryPos = commandHistory.length;
      commandInput.value = '';
    }
  }
});
