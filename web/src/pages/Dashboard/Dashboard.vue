<template>

    <Page ref="dashboardPage" title="Dashboard">
        <template v-slot:loading>
            <v-col cols="12" md="6" v-for="i in 4" :key="i">
                <v-card class="mx-1 mb-1">
                    <v-skeleton-loader class="mx-auto pa-3" type="card"></v-skeleton-loader>
                </v-card>
            </v-col>
        </template>

        <template v-slot:data>
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
        </template>

    </Page>

</template>

<script>

import { mapState } from 'vuex';

import mixins from '@/services/mixins';

import Page from '@/components/Page/Page';

export default {
    name: "Dashboard",
    mixins: [mixins],
    components: { Page },
    watch: {
        'cameras': function() {
            this.page('dashboardPage').data();
        }
    },
    computed: {
        ...mapState(['cameras']),
    },
    methods: {
    },
    mounted() {
        if (this.cameras) {
           this.page('dashboardPage').data();
        }
    },
};
</script>

