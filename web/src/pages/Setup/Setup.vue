<template>

    <Page ref="setupPage" title="Setup">

        <template v-slot:loading>
            <v-col cols="12" md="6" v-for="i in 4" :key="i">
                <v-card class="mx-1 mb-1">
                    <v-skeleton-loader class="mx-auto pa-3" type="card"></v-skeleton-loader>
                </v-card>
            </v-col>
        </template>

        <template v-slot:data>
            <v-col cols="12" md="6" v-for="host in hosts" :key="host">
            <v-card class="mx-1 mb-1">
                <v-card-title class="pa-6 pb-3">
                <p> {{ host }}</p>
                <v-spacer></v-spacer>
                </v-card-title>
                <v-card-text class="pa-6 pt-0">
                <v-row no-gutters>
                    <v-col cols="12">


                    <v-btn v-show="!isAlreadySetup(host)" color="primary" dark @click="show(host)">
                        Setup
                    </v-btn>
                    <v-btn v-show="isAlreadySetup(host)" disabled>
                        <v-icon left>mdi-check</v-icon>
                        Added
                    </v-btn>

                    </v-col>
                </v-row>
                </v-card-text>
            </v-card>
            </v-col>
        </template>

        <v-dialog v-model="dialog" persistent max-width="600px">
            <v-card>
            <v-card-title>
                <span class="headline">User Profile</span>
            </v-card-title>
            <v-card-text>
                <v-container>
                <v-row>
                    <v-col cols="12">
                        <v-text-field v-model="camera.name" label="Camera name" required></v-text-field>
                    </v-col>
                    <v-col cols="12">
                        <v-text-field v-model="camera.host" label="Host" requires></v-text-field>
                    </v-col>
                    <v-col cols="12">
                        <v-text-field v-model="camera.username" label="Username"></v-text-field>
                    </v-col>
                    <v-col cols="12">
                        <v-text-field v-model="camera.password" label="Password" type="password"></v-text-field>
                    </v-col>
                </v-row>
                </v-container>
            </v-card-text>
            <v-card-actions>
                <v-spacer></v-spacer>
                <v-btn color="blue darken-1" text @click="dialog = false">
                    Close
                </v-btn>
                <v-btn color="blue darken-1" text @click="save()">
                    Save
                </v-btn>
            </v-card-actions>
            </v-card>
        </v-dialog>

    </Page>

</template>

<script>

import { mapGetters, mapMutations } from 'vuex';

import apiClient from '@/services/api_client';
import mixins from '@/services/mixins';

import Page from '@/components/Page/Page';

export default {
    name: 'Setup',
    mixins: [mixins],
    components: { Page },
    data() {
        return {
            hosts: [],
            dialog: false,
            camera: {
                name: "",
                host: "",
                username: "",
                password: ""
            }
        }
    },
    mounted() {
        apiClient.discovery().then(response => {
            this.hosts = response.results;
            this.page('setupPage').data();
        }).catch(error => {
            var message = error.response && error.response.data ? error.response.data.message : error;
            this.page('setupPage').error(message);
        });
    },
    methods: {
        ...mapMutations(['setCameras']),
        ...mapGetters(['getCameras']),
        show(host) {
            this.camera = {
                name: "",
                host: host,
                username: "",
                password: ""
            }
            this.dialog = true;
        },
        save() {
            apiClient.addCamera(this.camera).then(() => {
                this.hosts = this.hosts.filter(host => host != this.camera.host);
                this.$toast.success("Camera was successfully added");
                this.dialog = false;
                apiClient.getCameras().then(response => {
                    this.setCameras(response.results);
                });
            }).catch(error => {
                var message = error.response && error.response.data ? error.response.data.message : error;
                this.$toast.error("Failed to add camera: " + message);
            });

        },
        isAlreadySetup(host) {
            const cameras = this.getCameras();
            var isSetup = false;
            cameras.forEach(camera => {
                const url = new URL(camera.manage_url);
                var hostCopy = host;

                if (!url.port && host.indexOf(':') != -1) {
                    hostCopy = host.split(':')[0]
                }

                if (url.host == hostCopy) {
                    isSetup = true;
                }
            });

            return isSetup;
        }
    }
};
</script>
