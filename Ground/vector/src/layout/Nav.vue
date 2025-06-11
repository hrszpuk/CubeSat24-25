<script setup>
    import { ref } from "vue";
    import Menubar from "primevue/menubar";
    
    const navItems = ref([
        {label: "Dashboard", icon: "pi pi-fw pi-home", to: "/"}        
    ]);
</script>

<template>
    <nav>
        <Menubar :model="navItems" breakpoint="1080px" :pt="{
            root: {
                class: 'border-none'
            },
            buttonIcon: {
                class: 'w-7 h-7'
            }
        }">
            <template #item="{item, label, props, root, hasSubmenu}">
                <RouterLink v-if="item.to" v-bind="props.action" :to="item.to">
                    <i v-bind="props.icon"></i>
                    <span v-bind="props.label">{{ label }}</span>
                </RouterLink>
                <a v-else v-bind="props.action" :href="item.href" :target="item.target">
                    <i v-bind="props.icon"></i>
                    <span v-bind="props.label">{{ label }}</span>
                    <i v-if="hasSubmenu" :class="['pi', { 'pi-angle-down': root, 'pi-angle-right': !root }]" v-bind="props.submenuicon"></i>
                </a>
            </template>
        </Menubar>
    </nav>
</template>