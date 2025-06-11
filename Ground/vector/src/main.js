import { createApp } from 'vue'
import router from './router';
import PrimeVue from 'primevue/config'
import Aura from '@primeuix/themes/aura'
import { definePreset } from '@primeuix/themes'
import ConfirmationService from 'primevue/confirmationservice'
import DialogService from 'primevue/dialogservice'
import ToastService from 'primevue/toastservice'
import App from './Main.vue'
import '@/assets/styles.scss'

const Noir = definePreset(Aura, {
    semantic: {
        primary: {
            50: "{neutral.50}",
            100: "{neutral.100}",
            200: "{neutral.200}",
            300: "{neutral.300}",
            400: "{neutral.400}",
            500: "{neutral.500}",
            600: "{neutral.600}",
            700: "{neutral.700}",
            800: "{neutral.800}",
            900: "{neutral.900}",
            950: "{neutral.950}"
        },
        colorScheme: {
            light: {
                primary: {
                    color: "{neutral.950}",
                    inverseColor: "#FFFFFF",
                    hoverColor: "{neutral.900}",
                    activeColor: "{neutral.800}"
                },
                highlight: {
                    background: "{neutral.950}",
                    focusBackground: "{neutral.700}",
                    color: "#FFFFFF",
                    focusColor: "#FFFFFF"
                }
            },
            dark: {
                primary: {
                    color: "{neutral.50}",
                    inverseColor: "{neutral.950}",
                    hoverColor: "{neutral.100}",
                    activeColor: "{neutral.200}"
                },
                highlight: {
                    background: "rgba(250, 250, 250, .16)",
                    focusBackground: "rgba(250, 250, 250, .24)",
                    color: "rgba(255, 255, 255, .87)",
                    focusColor: "rgba(255, 255, 255, .87)"
                }
            }
        }
    },
    components: {
        button: {
            padding: {
                x: "0.5em",
                y: "0.5em"
            },
            label: {
                font: {
                    weight: 600
                }
            }
        },
        confirmdialog: {
            icon: {
                size: "5rem"
            }
        },
        paginator: {
            jump: {
                to: {
                    page: {
                        input: {
                            max: {
                                width: "4rem"
                            }
                        }
                    }
                }
            }
        }
    }
});

createApp(App)
    .use(router)
    .use(PrimeVue, {
        theme: {
            preset: Noir,
            options: {
                darkModeSelector: 'system'
            }
        }
    })
    .use(ConfirmationService)
    .use(DialogService)
    .use(ToastService)
    .mount('#app')