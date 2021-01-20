<template>
    <v-app-bar
        class="main-header"
        height="64"
        fixed
        color='primary'
        dark>
        <v-btn icon class="mx-1" @click.stop="TOGGLE_DRAWER">
            <template v-if="DRAWER_STATE">
                <v-icon  style="font-size: 28px">mdi-arrow-left</v-icon>
            </template>
            <template v-else>
                <v-icon style="font-size: 28px">mdi-menu</v-icon>
            </template>
        </v-btn>
        <v-toolbar-title>Camera server</v-toolbar-title>
        <v-spacer></v-spacer>

        <v-menu
            min-width="180"
            offset-y
            bottom
            left
            nudge-bottom="10">
            <template v-slot:activator="{ on, attrs }">
            <v-btn
                class="mr-0"
                icon
                v-bind="attrs"
                v-on="on">
                <v-icon
                style="font-size: 28px"
                :color="config.light.iconColor">mdi-account</v-icon>
                </v-btn>
            </template>
            <v-list >
            <div class="text-h5 grey--text text--darken-3 px-4 pt-4">Admin</div>
            <div class="d-flex justify-center my-3">
                <v-btn width="80%" large outlined color="primary" class="text-capitalize" @click="signOut">Sign Out</v-btn>
            </div>
            </v-list>
        </v-menu>
    </v-app-bar>
</template>

<script>
import {mapActions, mapState} from 'vuex'
import config from '@/config';
import auth from '@/services/auth';

export default {
    name: 'Header',
    data: () => ({
        config,
    }),
    computed: {
        ...mapState(['drawer']),
        DRAWER_STATE :{
            get() {
                return this.drawer
            },
        }
    },
    methods: {
        ...mapActions([ 'TOGGLE_DRAWER' ]),
        signOut: function () {
            auth.signOut();
            this.$router.push('/login');
        }
    }
};
</script>

<style src="./Header.scss" lang="scss"></style>
