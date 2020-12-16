import Vue from 'vue';
import Router from 'vue-router';

import Layout from '@/components/Layout/Layout';

// Pages
import Dashboard from '@/pages/Dashboard/Dashboard';
import Login from "@/pages/Login/Login";
import Camera from "@/pages/Camera/Camera";

Vue.use(Router);

export default new Router({
    routes: [
        {
            path: '/login',
            name: 'Login',
            component: Login
        },
        {
            path: '/',
            redirect: 'login',
            name: 'Layout',
            component: Layout,
            children: [
                {
                    path: 'dashboard',
                    name: 'Dashboard',
                    component: Dashboard,
                },
                {
                    path: 'camera/:name',
                    name: 'Camera',
                    component: Camera
                },
            ],
        },
        {
            path: '*',
            name: 'Error',
            component: Error
        }
    ],
});
