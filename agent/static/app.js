async function sendMessage() {
    const input = document.getElementById('message-input');
    const message = input.value.trim();
    
    if (message) {
        print_message(message, "human")
        input.value = '';
        
        const response = await fetch(`/prompt`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ prompt: message })
        });

        const data = await response.json();
        print_message(data.response, "ai")
    }
}

function print_message(message, type) {
    const divclass = type === "human" ? "alert alert-primary ms-auto" : "alert alert-secondary";
    const messagesContainer = document.getElementById('chat-messages');
    messagesContainer.innerHTML += `<div class="${divclass}" style="max-width:80%">${message}</div>`;

    const chat = document.getElementById("chat-messages")
    chat.scrollTop = chat.scrollHeight
}


async function fetchMessagesAndPrint() {
    const response = await fetch('/prompt')
    let messages = await response.json()

    messages.forEach( message => {
        print_message(message.prompt, message.type)
    })
}

async function fetchNotifications() {
    const response = await fetch(`/staff_notifications`);
    const notifications = await response.json();
    displayNotifications(notifications);
}

function displayNotifications(notifications) {
    const notificationsList = document.getElementById('notifications-list');
    notificationsList.innerHTML = notifications.map(notification => `
        <div class="alert alert-primary mb-2">
            <div class="d-flex justify-content-between align-items-start">
                <div>
                    <strong>${notification.notifier_role}</strong>
                    <p class="mb-0">${notification.description}</p>
                </div>
                <small class="text-muted">${new Date(notification.time).toLocaleString()}</small>
            </div>
        </div>
    `).join('');
}

document.addEventListener('DOMContentLoaded', async () => {
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });
    sendButton.addEventListener('click', sendMessage);

    await fetchMessagesAndPrint();
    await fetchNotifications();
    setInterval(fetchNotifications, 5000);
});