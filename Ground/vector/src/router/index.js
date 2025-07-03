import { createRouter, createWebHistory } from 'vue-router'
import Layout from '@/layout/Layout.vue'

const router = createRouter({
    history: createWebHistory(),
    routes: [
        {
            path: "/",
            component: Layout,
            children: [
                {
                    path: "/",
                    name: "Dashboard",
                    component: () => import("@/views/Dashboard.vue")
                }
            ]
        }
    ]
});

export default router;