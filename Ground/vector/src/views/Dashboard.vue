<script setup>
    import { onMounted, onBeforeUnmount, reactive, ref, watch } from 'vue';
    import { useDateFormat, useFileSystemAccess, useNow } from '@vueuse/core';    
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
    const { isSupported, data, saveAs } = useFileSystemAccess();
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

                        if (isSupported) {
                            data.value = fileBlob;
                            saveAs({suggestedName: fileMetadata.name});
                        } else {
                            let fileURL = URL.createObjectURL(fileBlob);
                            let downloading = browser.downloads.download({
                                url: fileURL,
                                filename: fileMetadata.name,
                                saveAs: true
                            });
                            downloading.then(() => URL.revokeObjectURL(fileURL), (error) => toast.add({severity: "error", summary: "File Download Error", detail: `Failed to download file ${fileMetadata.name}: ${error}`, life: 3000}))
                        }
                    }
                    messages.value.push(obj.data);
                    toast.add({severity: "info", summary: "Message from CubeSat", detail: obj.data, life: 3000})
                    break;
                case "filemetadata":
                    fileMetadata.size = obj.size;
                    fileMetadata.name = obj.name;
                    break;
                case "filedata":
                    fileData.value.push(decodeURIComponent(atob(obj.data)))
                    break;
            }
        }
    );

    function handleCommand(message) {
        let response;
        console.log(`Command received: ${message}`);
        let msg = message.split(" ");
        let cmd = msg[0];
        let args = msg.slice(1);

        switch(cmd) {
            case "connect":
                let ip = args[0];
                response = establishConnection(ip);

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
                <code v-else v-for="message in messages" class="block">{{ message }}</code>
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