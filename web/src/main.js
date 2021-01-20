import Vue from 'vue'
import App from './App.vue'
import router from './Routes'
import store from './store/index'
import vuetify from './plugins/vuetify'
import Toast from "vue-toastification";
import "vue-toastification/dist/index.css";

Vue.use(Toast);
Vue.use(require('vue-moment'));

new Vue({
    vuetify,
    router,
    render: h => h(App), store
}).$mount('#app')
