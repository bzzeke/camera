import Vue from 'vue';
import Router from 'vue-router';

import Layout from '@/components/Layout/Layout';
import Dashboard from '@/pages/Dashboard/Dashboard';
import Login from "@/pages/Login/Login";
import Camera from "@/pages/Camera/Camera";
import Setup from "@/pages/Setup/Setup";
import Clips from "@/pages/Clips/Clips";
import Settings from "@/pages/Settings/Settings";

import auth from "@/services/auth";

Vue.use(Router);

const router = new Router({
    routes: [
        {
            path: '/login',
            name: 'Login',
            component: Login,
            meta: {
                public: true
            }
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
                },
                {
                    path: 'settings',
                    name: 'Settings',
                    component: Settings
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

router.beforeEach((to, from, next) => {
    const isPublic = to.matched.some(record => record.meta.public)
    const isAuthenticated = auth.isAuthenticated();

    if (!isPublic && !isAuthenticated) {
        return next({
            path:'/login'
        });
    }

    if (isAuthenticated && isPublic) {
      return next('/')
    }

    next();
});

export default router;
