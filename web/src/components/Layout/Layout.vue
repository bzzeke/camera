<template>
    <v-app class="pa-6">
        <Header />
        <Sidebar />
        <v-main class="content">
            <router-view />
        </v-main>
    </v-app>
</template>

<script>
    import Header from '@/components/Header/Header';
    import Sidebar from '@/components/Sidebar/Sidebar';
    import './Layout.scss';
    import apiClient from '../../api_client';
    import { mapMutations } from 'vuex'


    export default {
        name: 'Layout',
        components: {Header, Sidebar },
        created() {
            apiClient
                .get('/camera_list')
                .then(response => {
                    this.setCameras(response.data.results);
                });
        },
        methods: {
            ...mapMutations(['setCameras'])
        }
    };
</script>

<style src="./Layout.scss" lang="scss" />
