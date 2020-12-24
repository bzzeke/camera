<template>
    <v-container fluid>
        <div class="dashboard-page">
        <v-row no-gutters class="d-flex justify-space-between mt-10 mb-6">
            <h1 class="page-title">Dashboard</h1>
        </v-row>

        <v-row>
            <v-col cols="12" md="6" v-for="camera in cameras" :key="camera.id">
            <v-card class="mx-1 mb-1">
                <v-card-title class="pa-6 pb-3">
                <p> {{ camera.name }}</p>
                <v-spacer></v-spacer>
                </v-card-title>
                <v-card-text class="pa-6 pt-0">
                <v-row no-gutters>
                    <v-col cols="12">
                    <v-img :src="camera.snapshot_url"></v-img>
                    </v-col>
                </v-row>
                </v-card-text>
            </v-card>
            </v-col>
        </v-row>

        </div>
    </v-container>
</template>

<script>

import { mapState } from 'vuex';

export default {
    name: "Dashboard",
    components: {
    },
    data() {
        return {
        };
    },
    computed: {
        ...mapState(['cameras']),
    },
    methods: {
    },
    mounted() {
    },
};
</script>

