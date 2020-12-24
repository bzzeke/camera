<template>

<v-container fluid>


    <v-row no-gutters class="d-flex justify-space-between mt-10 mb-6">
        <h1 class="page-title">{{ this.cameraName }}: settings</h1>

        <div>
            <v-btn color="primary" class="text-capitalize" @click="save()">Save</v-btn>
        </div>

    </v-row>

    <v-row>
        <v-col cols="12">
            <v-tabs>
                <v-tab href="#options">Detection options</v-tab>

                <v-tab-item value="options">
                    <v-skeleton-loader v-if="!camera" class="mx-auto pa-3" type="card"></v-skeleton-loader>
                    <v-card v-if="camera">
                        <v-card-text>
                            <v-row>
                                <v-col cols="8">
                                    <div class="img-overlay-wrap">
                                        <img :src="snapshotURL" :width="width" :height="height">
                                        <svg class="container_svg" :viewBox="viewBox"></svg>
                                    </div>
                                </v-col>
                                <v-col cols="4">
                                    <v-row>
                                        <v-col>
                                            <v-btn color="secondary" class="text-capitalize mr-2" @click="clear()" :disabled="!enableClear">Clear zone</v-btn>
                                        </v-col>
                                    </v-row>
                                            <v-row>
                                            <v-col>
                                                <v-checkbox v-model="camera.detection.enabled" label="Enable detection"></v-checkbox>
                                            </v-col>
                                            </v-row>
                                            <v-row>
                                            <v-col>
                                                <v-select v-model="camera.detection.valid_categories" :items="categories" multiple label="Categories">
                                                    <template v-slot:prepend-item>
                                                        <v-list-item ripple @click="selectedCategories = []">
                                                        <v-list-item-content>
                                                            <v-list-item-title>
                                                            Any
                                                            </v-list-item-title>
                                                        </v-list-item-content>
                                                        </v-list-item>
                                                        <v-divider class="mt-2"></v-divider>
                                                    </template>
                                                </v-select>
                                            </v-col>
                                        </v-row>
                                </v-col>
                            </v-row>
                        </v-card-text>
                    </v-card>
                </v-tab-item>

            </v-tabs>
        </v-col>
    </v-row>

</v-container>
</template>

<script>

import Zone from '../../logic/zone';
import apiClient from '../../api_client';
import { mapGetters } from 'vuex';

export default {
    name: 'Camera',
    data() {
        return {
            zone: null,
            categories: [
                'Person',
                'Car'
            ]
        }
    },
    mounted() {
        this.createZone()
    },
    watch: {
        '$route.params.id': function () {
            this.createZone()
        }
    },
    computed: {
        ...mapGetters(['getCamera']),
        camera() {
            return this.getCamera(this.$route.params.id) || {"detection": {
                "enabled": false,
                "valid_categories": [],
                "zone": []
            }};
        },
        width() {
            if (this.camera.meta == null) {
                return 0
            }
            return parseInt(this.camera.meta.width / 2);
        },
        height() {
            if (this.camera.meta == null) {
                return 0
            }

            return parseInt(this.camera.meta.height / 2);
        },
        viewBox() {
            return '0 0 ' + this.width + ' ' + this.height;
        },
        snapshotURL() {
            return this.camera.snapshot_url || "";
        },
        cameraName() {
            return this.camera.name || "";
        },
        enableClear() {
            return this.zone !== null && this.zone.get() != false;
        }
    },
    methods: {

        createZone() {
            this.zone = new Zone(this.camera);
        },
        clear() {
            this.zone.clearPoligon();
        },
        save() {
            let zone = this.zone.get();
            if (zone === false) {
                this.$toast.error("Failed to save zone: please finish editing first");
                return;
            }

            this.camera.detection.zone = zone;


            apiClient.saveOptions(this.camera.id, this.camera.detection).then(() => {
                this.$toast.success("Options were saved successfully");
            }).catch(error => {
                var message = error.response && error.response.data ? error.response.data.message : error;
                this.$toast.error("Failed to options: " + message);
            });
        },

    }
};
</script>


<style>
.img-overlay-wrap {
  position: relative;
  display: inline-block; /* <= shrinks container to image size */
  transition: transform 150ms ease-in-out;
}

.img-overlay-wrap img { /* <= optional, for responsiveness */
   display: block;
   max-width: 100%;
   height: auto;
}

.img-overlay-wrap svg {
  position: absolute;
  top: 0;
  left: 0;
}

</style>