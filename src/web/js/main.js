
const chatContainer = document.getElementById("messages");

const observer = new MutationObserver(() => {
    setTimeout(() => {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }, 100); 
});

observer.observe(chatContainer, { childList: true, subtree: true });

// --- TOGGLE INPUT (Called by Python) ---
eel.expose(toggleInput);
function toggleInput(show) {
    let input = document.getElementById("userInput");
    let btn = document.getElementById("userInputButton");
    let voiceUI = document.querySelector(".voice-interface"); // Grab the voice wave
    
    if (show) {
        input.style.display = "block";
        btn.style.display = "flex"; // Fixes button alignment
        if(voiceUI) voiceUI.style.display = "none"; // Hide voice UI to prevent overlap
        input.focus();
    } else {
        input.style.display = "none";
        btn.style.display = "none";
        if(voiceUI) voiceUI.style.display = "flex"; // Show voice UI again
    }
}

// --- EXISTING LOGIC ---
eel.expose(addUserMsg);
function addUserMsg(msg) {
    let element = document.getElementById("messages");
    element.innerHTML += '<div class="message from">' + msg + '</div>';
}

eel.expose(addAppMsg);
function addAppMsg(msg) {
    let element = document.getElementById("messages");
    element.innerHTML += '<div class="message to">' + msg + '</div>';
}

function getUserInput() {
    let element = document.getElementById("userInput");
    let msg = element.value.trim();
    if (msg.length !== 0) {
        element.value = "";
        eel.getUserInput(msg);
    }
}

document.getElementById("userInputButton").addEventListener("click", getUserInput, false);
document.getElementById("userInput").addEventListener("keyup", function (event) {
    if (event.keyCode === 13) { getUserInput(); }
});

function switchBackend() {
    let mode = document.getElementById("backendToggle").value;
    
    // Call the Python endpoint
    eel.set_llm_backend(mode);
    
    // Give the user visual feedback
    let chatContainer = document.getElementById("messages");
    chatContainer.innerHTML += `<div class="message system" style="text-align: center; color: #94a3b8; font-size: 0.8rem; width: 100%; margin: 10px 0;">[System: Engine routed to ${mode}]</div>`;
}