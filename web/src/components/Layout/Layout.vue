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
    import { mapMutations } from 'vuex'

    import apiClient from '@/services/api_client';

    import Header from '@/components/Header/Header';
    import Sidebar from '@/components/Sidebar/Sidebar';

    export default {
        name: 'Layout',
        components: {Header, Sidebar },
        created() {
            apiClient.getCameras().then(response => {
                this.setCameras(response.results);
            });
        },
        methods: {
            ...mapMutations(['setCameras'])
        }
    };
</script>

<style src="./Layout.scss" lang="scss" />
