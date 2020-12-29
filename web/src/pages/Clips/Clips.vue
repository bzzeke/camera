<template>

    <Page ref="clipsPage" title="Clips">
        <template v-slot:toolbar>
            <v-row>
                <v-col cols="12">
                    <v-card class="mx-1 mb-1 pl-2 pr-2">
                        <v-row>
                            <v-col cols="12" sm="6" md="4">
                                <v-menu ref="menu" v-model="menu" :close-on-content-click="false"  transition="scale-transition" offset-y min-width="290px">
                                <template v-slot:activator="{ on, attrs }">
                                    <v-text-field v-model="filters.date" label="Select date" prepend-icon="mdi-calendar" readonly v-bind="attrs" v-on="on"></v-text-field>
                                </template>
                                <v-date-picker v-model="filters.date" no-title scrollable @input="menu = false">
                                </v-date-picker>
                                </v-menu>
                            </v-col>
                            <v-spacer></v-spacer>
                            <v-col cols="12" sm="6" md="4">
                                <v-select v-model="filters.category" :items="categories" label="Categories"></v-select>
                            </v-col>
                            <v-spacer></v-spacer>
                            <v-col cols="12" sm="6" md="4">
                                <v-select v-model="filters.camera" :items="cameras" label="Camera"></v-select>
                            </v-col>
                            <v-spacer></v-spacer>
                        </v-row>
                    </v-card>
                </v-col>
            </v-row>
        </template>

        <template v-slot:loading>
        </template>

        <template v-slot:data>
            <v-card class="mx-1 mb-1 pl-2 pr-2">
                <v-row v-for="clip in clips" :key="clip.timestamp">
                    <v-col cols="12" md="6">
                    <v-card class="mx-1 mb-1">
                        <v-row>
                        <v-col cols="5">

                            <v-dialog v-model="dialog" max-width="600px">

                                <template v-slot:activator="{ on, attrs }">
                                    <v-img :src="clip.thumbnail_url" v-bind="attrs" v-on="on"></v-img>
                                </template>
                                <v-card>
                                <v-card-text>
                                    <v-container>
                                        <video width="320" height="240" controls>
                                            <source :src="clip.video_url" type="video/mp4">
                                        </video>
                                    </v-container>
                                </v-card-text>
                                <v-card-actions>
                                    <v-spacer></v-spacer>
                                    <v-btn color="blue darken-1" text @click="dialog = false">
                                        Close
                                    </v-btn>
                                </v-card-actions>
                                </v-card>
                            </v-dialog>
                        </v-col>
                        <v-col cols="3">
                            <p>{{ clip.camera }}</p>
                            <p>{{ formatDate(clip.timestamp) }}</p>
                            <p>{{ formatObjects(clip.objects) }}</p>
                        </v-col>
                        </v-row>
                    </v-card>
                    </v-col>
                </v-row>
            </v-card>
        </template>
    </Page>
</template>

<script>

import { mapGetters } from 'vuex';

import apiClient from '@/services/api_client';
import mixins from '@/services/mixins';

import Page from '@/components/Page/Page';

export default {
    name: 'Clips',
    mixins: [mixins],
    components: { Page },
    data() {
        return {
            clips: [],
            dialog: false,
            objectIcons: {
                person: "🚶🏻‍♂️",
                car: "🚗",
                bus: "🚌 ",
                truck: "🚚",
                motorcycle: "🏍",
                bicycle: "🚲 "
            },
            categories: [
                "All objects",
                "person",
                "car",
                "bus"
            ],
            menu: false,
            filters: {
                date: new Date().toISOString().substr(0, 10),
                category: "All objects",
                camera: "Any camera"
            }
        }
    },
    mounted() {
        this.getClips();
    },
    watch: {
        "filters": {
            handler(){
                this.getClips();
            },
            deep: true
        }
    },
    computed: {
        "cameras": function() {
            let cameras = this.getCameras().map((camera) => {
                return camera.name
            });

            cameras.unshift("Any camera");

            return cameras;
        }
    },
    methods: {
        ...mapGetters(['getCameras']),
        getClips() {
            apiClient.getClips(this.filters).then(response => {
                this.clips = response.results;
                this.page('clipsPage').data();
            }).catch(error => {
                var message = error.response && error.response.data ? error.response.data.message : error;
                this.page('clipsPage').error(message);
            });

        },
        formatObjects(objects) {
            var icons = objects.map((key) => {
                return this.objectIcons[key];
            });

            return icons.join(" ");
        },
        formatDate(timestamp) {
            let date = new Date(timestamp * 1000);
            return this.$moment(date).format("hh:mm:ss");
        }
    }
};
</script>
