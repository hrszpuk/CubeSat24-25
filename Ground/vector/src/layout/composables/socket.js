import { computed, reactive } from 'vue';
import { useWebSocket } from '@vueuse/core';
import TerminalService from 'primevue/terminalservice';

const connection = reactive({
    ip: "127.0.0.1",
    port: 80,
    url: "ws://127.0.0.1:80"
});

const { ws, status, data, send, open, close } = useWebSocket(computed(() => connection.url), {
    immediate: false,
    autoReconnect: {
        retries: 3, 
        delay: 250, 
        onFailed() {
            alert(`Failed to connect WebSocket on ${connection.ip}:${connection.port} after 3 retries`);
        }
    },
    heartbeat: true,
    onConnected(ws) {
        console.log(`Successfully conencted to CubeSat on ${connection.ip}:${connection.port}`);
    },        
    onDisconnected(ws, event) {
        if (event.wasClean) {
            console.log("Successfully disconnected from CubeSat");
        }
    },
    onError(ws, event) {
        console.log(`Error connecting to CubeSat on ${connection.ip}:80`)
    },
    onMessage(ws, event) {
        console.log(`Message from CubeSat: ${event}`);
    }
});

export function useSocket() {
    const getStatus = () => status.value

    const establishConnection = (ip, port) => {
        connection.ip = ip ? ip : connection.ip;
        connection.port = port ? port : connection.port;
        connection.url = `ws://${connection.ip}:${connection.port}`;

        return `Connecting to CubeSat on ${connection.ip}:${connection.port}...`
    }

    const sendMessage = (msg) => {
        send(msg);
        console.log(`Sent message ${msg} to CubeSat`)

        return `CubeSat: ${data}`
    }

    const dropConnection = () => {
        close()
        console.log("Successfully disconnected from CubeSat")
    }

    return {connection, getStatus, open, establishConnection, sendMessage, data, dropConnection}
}