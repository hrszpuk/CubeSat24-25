<script setup>
    import { onMounted, onBeforeUnmount, reactive, ref, watch, markRaw } from 'vue';
    import { useDateFormat, useNow } from '@vueuse/core';
    import { useAudio } from '@/layout/composables/audio.js';
    import { useDialog } from 'primevue/usedialog';
    import { useSocket } from '@/layout/composables/socket.js';
    import { useToast } from '@/layout/composables/toast.js';
    import ArgumentsDialog from '@/components/ArgumentsDialog.vue';
    import DialogFooter from '@/components/DialogFooter.vue';
    import Button from 'primevue/button';
    import Card from 'primevue/card';
    import Message from 'primevue/message';
    import ProgressDialog from '@/components/ProgressDialog.vue';
    import ScrollPanel from 'primevue/scrollpanel';
    import SplitButton from 'primevue/splitbutton';
    import Tag from 'primevue/tag';
    import Terminal from 'primevue/terminal';
    import TerminalService from 'primevue/terminalservice';
    import Toolbar from 'primevue/toolbar';
    
    const { getStatus, establishConnection, sendMessage, data, dropConnection } = useSocket();
    const { playLogSfx } = useAudio();
    const dialog = useDialog();
    const toast = useToast();
    const dateToday = useDateFormat(useNow(), "DD/MM/YYYY");
    const timeNow = useDateFormat(useNow(), "HH:mm:ss");
    const phase3Subphases = [{label: "Start Phase 3a", command: () => sendMessage("start_phase 3 a")}, {label: "Start Phase 3b", command: () => sendMessage("start_phase 3 b")}, {label: "Start Phase 3c", command: () => sendMessage("start_phase 3 c")}]
    const logs = ref([]);
    const messages = ref([]);
    const cubeSatData = ref([]);
    const fileMetadata = reactive({
        size: null,
        name: null,
    });
    const fileData = ref([]);
    const receivedBytes = ref(0);

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

    function phase2Button() {
        dialog.open(ArgumentsDialog, {
            props: {header: "Enter Sequence for Phase 2", modal: true},
            templates: {
                footer: markRaw(DialogFooter)
            },
            data: {
                submitFunction: (record) => {
                    sendMessage(`start_phase 2 ${record.sequence}`);
                },
                fields: [
                    { id: "sequence", label: "Sequence", required: true }
                ],
                record: {},
                hasSubmitted: false
            }
        });
    }

    onMounted(() => TerminalService.on("command", handleCommand));

    watch(
        data,
        data => {
            if (typeof data === "string") {
                if (!data.localeCompare("File transfer started")) {
                    fileData.value = [];
                    receivedBytes.value = 0;
                    dialog.open(ProgressDialog, {
                        props: {header: "Receiving File from CubeSat...", modal: true, closable: false},
                        data: {
                            progress: receivedBytes,
                            total: fileMetadata.size
                        }
                    });
                } else if (!data.localeCompare("File transfer complete")) {
                    const file = new File(fileData.value, fileMetadata.name, {type: "application/zip"});
                    const fileURL = URL.createObjectURL(file);
                    const elem = document.createElement("a");
                    elem.href = fileURL;
                    elem.download = fileMetadata.name;
                    document.body.appendChild(elem);
                    elem.click();
                    document.body.removeChild(elem);
                    URL.revokeObjectURL(fileURL);
                    toast.add({severity: "info", summary: "File from CubeSat", detail: `Received file ${fileMetadata.name}`, life: 3000})
                } else if (data.localeCompare("pong")) {
                    let obj = JSON.parse(data);
                    
                    switch(obj.type) {
                        case "log":
                            playLogSfx();
                            logs.value.unshift(obj.data);
                            break;
                        case "data":
                            cubeSatData.value.unshift(obj.data);
                            break;
                        case "message":
                            messages.value.unshift(obj);
                            toast.add({severity: "info", summary: "Message from CubeSat", detail: obj.data, life: 3000})
                            break;
                        case "filemetadata":
                            fileMetadata.size = obj.data.size;
                            fileMetadata.name = obj.data.name;
                            break;
                    }
                }
            } else {
                if (data instanceof Blob) {
                    fileData.value.push(data);
                    receivedBytes.value += data.size;
                }
            }
        }
    );

    onBeforeUnmount(() => TerminalService.off("command", handleCommand));
</script>

<template>    
    <section class="grid grid-cols-12 gap-4">
        <Toolbar class="col-span-12">
            <template #center>
                <section class="flex flex-wrap gap-2">
                    <Button label="Start Phase 1" :disabled="getStatus() !== 'OPEN'" @click="sendMessage('start_phase 1')"></Button>
                    <Button label="Start Phase 2" :disabled="getStatus() !== 'OPEN'" @click="phase2Button"></Button>
                    <SplitButton label="Start Phase 3" :model="phase3Subphases" :disabled="getStatus() !== 'OPEN'"></SplitButton>
                    <Button severity="danger" label="Stop Phase" :disabled="getStatus() !== 'OPEN'"></Button>
                </section>
            </template>
        </Toolbar>        
        <section class="col-span-12 xl:col-span-3">
            <Card>
                <template #title>Status</template>
                <template #content>
                    <ScrollPanel style="width: 100%; height: 210px">
                        <code class="block">Date: {{ dateToday }}</code>
                        <code class="block">Time: {{ timeNow }}</code>
                        <code class="block">Connection: <Tag :severity="getStatus() === 'CONNECTING'  ? 'info' : getStatus() === 'OPEN' ? 'success' : 'danger'" :value="getStatus() === 'CONNECTING'  ? 'CONNECTING' : getStatus() === 'OPEN' ? 'ONLINE' : 'OFFLINE'"></Tag></code>
                    </ScrollPanel>
                </template>
            </Card>
        </section>
        <section class="col-span-12 xl:col-span-6">
            <Terminal welcomeMessage="Vector Terminal" prompt=">"></Terminal>
        </section>
        <section class="col-span-12 xl:col-span-3">
            <Card>
                <template #title>Messages</template>
                <template #content>
                    <ScrollPanel style="width: 100%; height: 210px">
                        <Message v-if="!messages.length" variant="simple" severity="secondary">No messages</Message>
                        <Message v-else v-for="message in messages" variant="simple" :severity="message.includes('ERROR') ? 'error': 'secondary'"><Tag :value="message.timestamp"></Tag> {{ message.data }}</Message>
                    </ScrollPanel>
                </template>
            </Card>
        </section>
        <section class="col-span-12">
            <Card>
                <template #title>Logs</template>
                <template #content>
                    <ScrollPanel style="width: 100%; height: 210px">
                        <Message v-if="!logs.length" variant="simple">No logs</Message>
                        <Message v-else v-for="log in logs" variant="simple" :severity="log.toLowerCase().includes('error') ? 'error': 'info'">{{ log }}</Message>
                    </ScrollPanel>
                </template>
            </Card>
        </section>
    </section>
</template>