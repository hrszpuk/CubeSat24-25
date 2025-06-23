import { computed, reactive } from 'vue';
import TerminalService from 'primevue/terminalservice';

const connection = reactive({
    ip: null,
    socket: null,
    connecting: false,
    online: false
});

const errorSocket = (err) => {
    connection.connecting = false;
    connection.socket = null;
    alert(`CubeSat connection error: ${err}`)
}

const openSocket = () => {
    connection.connecting = false;
    connection.online = true;
    TerminalService.emit("response", `Successfully conencted to CubeSat at ${connection.ip}`)
}

const closeSocket = () => {
    connection.ip = null;
    connection.socket = null;
    connection.online = false;
}

export function useSocket() {
    const establishConnection = (ip, message_handler) => {        
        connection.ip = ip;

        try {
            connection.socket = new WebSocket(`ws://${ip}:80`);
            connection.socket.onerror = errorSocket;
            connection.socket.onopen = openSocket;
            connection.socket.onmessage = message_handler;
            connection.socket.onclose = closeSocket;
            connection.connecting = true;

            return `Attempting to conenct to CubeSat at ${ip}:80...`
        } catch(err) {
            connection.connecting = false;

            return `Failed to connect to CubeSat: ${err}`
        }
    }

    const sendMessage = (message) => {
        try {
            connection.socket.send(message);
        } catch(err) {
            return `Failed to send ${message} to CubeSat: ${err}`
        }
    }

    const dropConnection = () => {
        try {
            connection.socket.close();
            connection.online = false;

            return "Successfully disconnected from CubeSat"
        } catch(err) {
            return `Failed to disconnect from CubeSat: ${err}`
        }
    }

    const isConnecting = computed(() => connection.connecting);
    const isOnline = computed(() => connection.online);

    return {isConnecting, isOnline, establishConnection, sendMessage, dropConnection}
}