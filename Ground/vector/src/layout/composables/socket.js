import { computed, reactive } from 'vue';
import { useWebSocket } from '@vueuse/core';
import { useToast } from './toast.js';
import { useAudio } from './audio.js';

const toast = useToast();
const {playConnectSfx, playErrorSfx, playMessageSfx, playDisconnectSfx} = useAudio();

const connection = reactive({
    ip: "172.20.10.9",
    port: 8000, 
    url: "ws://172.20.10.9:8000"
});

const { ws, status, data, send, open, close } = useWebSocket(computed(() => connection.url), {
    immediate: false,
    autoConnect: false,
    autoReconnect: {
        retries: 3, 
        delay: 500, 
        onFailed() {
            playErrorSfx();
            toast.add({severity: "error", summary: "WebSocket Error", detail: `Failed to connect WebSocket on ${connection.ip}:${connection.port} after 3 retries`, life: 3000});
        }
    },
    heartbeat: false,
    onConnected(ws) {
        playConnectSfx();
        toast.add({severity: "success", summary: "WebSocket Connected", detail: `Successfully conencted to CubeSat on ${connection.ip}:${connection.port}`, life: 3000});
    },        
    onDisconnected(ws, event) {        
        if (event.wasClean) {
            playDisconnectSfx();
            toast.add({severity: "success", summary: "WebSocket Disconnected", detail: "Successfully disconnected from CubeSat", life: 3000});
        }
    },
    onError(ws, event) {
        playErrorSfx();
        toast.add({severity: "error", summary: "WebSocket Error", detail: `Error connecting to CubeSat on ${connection.ip}:${connection.port}`, life: 3000});
    },
    onMessage(ws, event) {
        // playMessageSfx()
        let obj = JSON.parse(event.data)
        
        if (obj.type.localeCompare("message") === 0) {
            console.log(`Message from CubeSat: ${obj.data}`);
        }

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
        if (status.value.localeCompare("OPEN") === 0) {
            send(msg);
            toast.add({severity: "success", summary: "Message Sent", detail: `Sent message ${msg} to CubeSat`, life: 3000});
        } else {
            playErrorSfx();
            toast.add({severity: "error", summary: "Send Message Error", detail: `Failed to send ${msg} to CubeSat: Not connected!`, life: 3000});
        }

        return `CubeSat: ${data}`
    }

    const dropConnection = () => {
        close()
    }

    return {connection, getStatus, establishConnection, sendMessage, message: data, dropConnection}
}