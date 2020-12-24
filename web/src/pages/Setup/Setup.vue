<template>
<v-container fluid>
    <v-row no-gutters class="d-flex justify-space-between mt-10 mb-6">
        <h1 class="page-title">Setup</h1>
    </v-row>
    <v-row>

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
    </v-row>

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
</v-container>

</template>

<script>

import apiClient from '../../api_client';
import { mapGetters, mapMutations } from 'vuex';

export default {
    name: 'Setup',
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
        /*apiClient.discovery().then(response => {
            this.hosts = response.results;
        }).catch(error => {
            var message = error.response && error.response.data ? error.response.data.message : error;
            this.$toast.error("Failed to run discovery: " + message);
        });*/
        this.hosts = [
            "10.10.10.1:80",
            "10.10.10.2:90",
            "10.10.10.4:80",
            "10.10.10.11:80",
            "10.10.10.21:80",
            "10.10.10.41:80",
            "10.10.10.15:80",
            "10.10.10.25:80",
            "10.10.10.45:80"
        ];
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
                apiClient.getCameras().then(response => {
                    this.setCameras(response.results);
                });
            }).catch(error => {
                var message = error.response && error.response.data ? error.response.data.message : error;
                this.$toast.error("Failed to add camera: " + message);
            });
            this.dialog = false;
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
