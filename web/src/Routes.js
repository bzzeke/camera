import Vue from 'vue';
import Router from 'vue-router';

import Layout from '@/components/Layout/Layout';

// Pages
import Dashboard from '@/pages/Dashboard/Dashboard';
import Login from "@/pages/Login/Login";
import Camera from "@/pages/Camera/Camera";
import Setup from "@/pages/Setup/Setup";
import Clips from "@/pages/Clips/Clips";

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
                    path: 'camera/:id',
                    name: 'Camera',
                    component: Camera
                },
                {
                    path: 'setup',
                    name: 'Setup',
                    component: Setup
                },
                {
                    path: 'clips',
                    name: 'Clips',
                    component: Clips
                }
            ],
        },
        {
            path: '*',
            name: 'Error',
            component: Error
        }
    ],
});
