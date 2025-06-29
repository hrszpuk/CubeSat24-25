<script setup>
    import { onMounted, onBeforeUnmount, reactive, ref, watch } from 'vue';
    import { useDateFormat, useNow } from '@vueuse/core';    
    import { useSocket } from '@/layout/composables/socket.js';
    import { useToast } from '@/layout/composables/toast.js';
    import Button from 'primevue/button';
    import Card from 'primevue/card';
    import ScrollPanel from 'primevue/scrollpanel';
    import SplitButton from 'primevue/splitbutton';
    import Terminal from 'primevue/terminal';
    import TerminalService from 'primevue/terminalservice';
    import Toolbar from 'primevue/toolbar';
    
    const { establishConnection, sendMessage, message, dropConnection } = useSocket();
    const toast = useToast();
    const dateToday = useDateFormat(useNow(), "DD/MM/YYYY");
    const timeNow = useDateFormat(useNow(), "HH:mm:ss");
    const phase3Subphases = [{label: "Start Phase 3a", command: () => sendMessage("start_phase 3 a")}, {label: "Start Phase 3b", command: () => sendMessage("start_phase 3 b")}, {label: "Start Phase 3c", command: () => sendMessage("start_phase 3 c")}]
    const logs = ref([]);
    const messages = ref([]);
    const fileMetadata = reactive({
        size: null,
        name: null,
    });
    const fileData = ref([]);    
    
    watch(
        message,
        message => {
            let obj = JSON.parse(message);            
            
            switch(obj.type) {
                case "log":
                    logs.value.push(obj.data);
                    break;
                case "message":
                    if (obj.data.localeCompare("File send complete") === 0) {
                        let fileBlob = new Blob(fileData.value);
                        let fileURL = URL.createObjectURL(fileBlob);
                        const elem = document.createElement("a");
                        elem.href = fileURL;
                        elem.download = fileMetadata.name;
                        document.body.appendChild(elem);
                        elem.click();
                        document.body.removeChild(elem);
                        URL.revokeObjectURL(fileURL);
                    }

                    messages.value.push(obj);
                    toast.add({severity: "info", summary: "Message from CubeSat", detail: obj.data, life: 3000})
                    break;
                case "filemetadata":
                    fileMetadata.size = obj.data.size;
                    fileMetadata.name = obj.data.name;
                    break;
                case "filedata":
                    let data = decodeURIComponent(atob(obj.data).split('').map(function(c) {
                        return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
                    }).join(''));
                    fileData.value.push(data);
                    break;                    
            }
        }
    );

    function handleCommand(message) {
        let response;
        let msg = message.split(" ");
        let cmd = msg[0];
        let args = msg.length > 1 ? msg.slice(1) : null;

        switch(cmd) {
            case "connect":
                if (args) {
                    let ip = args[0];
                    response = establishConnection(ip);
                } else {
                    response = "No IP provided!";
                }

                break;
            case "disconnect":
                response = dropConnection();
                
                break;        
            default:
                sendMessage(message)
        }

        TerminalService.emit("response", response)
    }

    onMounted(() => {
        TerminalService.on("command", handleCommand)
    })

    onBeforeUnmount(() => {
        TerminalService.off("command", handleCommand)
    })
</script>

<template>    
    <Toolbar>
        <template #center>
            <Button class="mr-2" label="Start Phase 1" @click="sendMessage('start_phase 1')"></Button>
            <Button class="mr-2" label="Start Phase 2" @click="sendMessage('start_phase 2')"></Button>
            <SplitButton class="mr-2" label="Start Phase 3" :model="phase3Subphases"></SplitButton>
            <Button severity="danger" label="Stop Phase"></Button>
        </template>
    </Toolbar>
    <Terminal welcomeMessage="Vector Terminal" prompt=">"></Terminal>
    <Card>
        <template #title>Log</template>
        <template #content>
            <ScrollPanel style="width: 100%; height: 200px">
                <code v-if="!logs.length" class="block">No log messages</code>
                <code v-else v-for="log in logs" class="block">{{ log }}</code>
            </ScrollPanel>
        </template>
    </Card>
    <Card>
        <template #title>Messages</template>
        <template #content>
            <ScrollPanel style="width: 100%; height: 200px">
                <code v-if="!messages.length" class="block">No messages from CubeSat</code>
                <code v-else v-for="message in messages" class="block">[{{ message.timestamp }}] {{ message.data }}</code>
            </ScrollPanel>
        </template>
    </Card>
    <Card>
        <template #title>Status</template>
        <template #content>
            <code class="block">Date: {{ dateToday }}</code>
            <code class="block">Time: {{ timeNow }}</code>
        </template>
    </Card>
</template>