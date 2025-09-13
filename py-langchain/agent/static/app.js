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
    }
}

function print_message(message, type) {
    const classes = {
        human: "alert alert-primary ms-auto",
        ai: "alert alert-secondary",
        interrupted: "alert alert-warning w-75 mx-auto text-center"
    }
    const divclass = classes[type]
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
    setInterval(fetchMessagesAndPrint, 5000);
    await fetchNotifications();
    setInterval(fetchNotifications, 5000);
});