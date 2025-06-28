import { computed, reactive } from 'vue';
import { useWebSocket } from '@vueuse/core';
import { useToast } from './toast.js';

const connect_sfx = new Audio("/connect_sfx.mp3");
const message_sfx = new Audio("/message_sfx.mp3")
const disconnect_sfx = new Audio("/disconnect_sfx.mp3");
const toast = useToast();

const connection = reactive({
    ip: "127.0.0.1",
    port: 8000, 
    url: "ws://127.0.0.1:8000"
});

const { ws, status, data, send, open, close } = useWebSocket(computed(() => connection.url), {
    immediate: false,
    autoConnect: false,
    autoReconnect: {
        retries: 3, 
        delay: 500, 
        onFailed() {
            toast.add({severity: "error", summary: "WebSocket Error", detail: `Failed to connect WebSocket on ${connection.ip}:${connection.port} after 3 retries`, life: 3000});
        }
    },
    heartbeat: true,
    onConnected(ws) {
        connect_sfx.play();
        toast.add({severity: "success", summary: "WebSocket Connected", detail: `Successfully conencted to CubeSat on ${connection.ip}:${connection.port}`, life: 3000});
    },        
    onDisconnected(ws, event) {        
        if (event.wasClean) {
            disconnect_sfx.play();
            toast.add({severity: "success", summary: "WebSocket Disconnected", detail: "Successfully disconnected from CubeSat", life: 3000});
        }
    },
    onError(ws, event) {
        toast.add({severity: "error", summary: "WebSocket Error", detail: `Error connecting to CubeSat on ${connection.ip}:${connection.port}`, life: 3000});
    },
    onMessage(ws, event) {
        //message_sfx.play()
        console.log(`Message from CubeSat: ${event}`);
    }
});

export function useSocket() {
    const getStatus = () => status.value

    const establishConnection = (ip, port) => {
        connection.ip = ip ? ip : connection.ip;
        connection.port = port ? port : connection.port;
        connection.url = `ws://${connection.ip}:${connection.port}`;
        open();

        return `Connecting to CubeSat on ${connection.ip}:${connection.port}...`
    }

    const sendMessage = (msg) => {
        send(msg);
        toast.add({severity: "success", summary: "Message Sent", detail: `Sent message ${msg} to CubeSat`, life: 3000});

        return `CubeSat: ${data}`
    }

    const dropConnection = () => {
        close()
    }

    return {connection, getStatus, establishConnection, sendMessage, message: data, dropConnection}
}