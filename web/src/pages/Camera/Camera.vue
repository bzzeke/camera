<template>

<Page ref="cameraPage" :title="title">

    <template v-slot:buttons>
        <div>

            <v-dialog v-model="removeDialog" persistent width="500">
                <template v-slot:activator="{ on, attrs }">
                    <v-btn color="secondary" class="text-capitalize mr-3" v-bind="attrs" v-on="on">Remove camera</v-btn>
                </template>

                <v-card>
                    <v-card-title class="headline">
                        Please confirm
                    </v-card-title>
                    <v-card-text>
                        Are you sure to remove camera?
                    </v-card-text>
                    <v-card-actions>
                        <v-spacer></v-spacer>
                        <v-btn color="secondary" text @click="removeDialog = false">
                            Cancel
                        </v-btn>
                        <v-btn color="primary" text @click="remove()">
                            Remove
                        </v-btn>
                    </v-card-actions>
                </v-card>
            </v-dialog>
            <v-btn color="primary" class="text-capitalize" @click="save()">Save</v-btn>
        </div>
    </template>

    <template v-slot:loading>
        <v-skeleton-loader class="mx-auto pa-3" type="card"></v-skeleton-loader>
    </template>

    <template v-slot:data>
        <v-col cols="12">
            <v-card class="mx-1 mb-1">
                <v-card-text>
                    <v-tabs>
                        <v-tab href="#options">Detection options</v-tab>
                        <v-tab-item value="options">
                            <v-row>
                                <v-col cols="8">
                                    <div class="img-overlay-wrap">
                                        <img :src="camera.snapshot_url" :width="camera.meta.width" :height="camera.meta.height">
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
                        </v-tab-item>
                    </v-tabs>
                </v-card-text>
            </v-card>
        </v-col>
    </template>
</Page>
</template>

<script>

import { mapGetters } from 'vuex';

import Zone from '@/services/zone';
import apiClient from '@/services/api_client';
import mixins from '@/services/mixins';

import Page from '@/components/Page/Page';


export default {
    name: 'Camera',
    mixins: [mixins],
    components: { Page },
    data() {
        return {
            zone: null,
            removeDialog: false,
            categories: [
                'Person',
                'Car'
            ]
        }
    },
    mounted() {
        if (this.camera == null) {
            return;
        }
        this.page('cameraPage').data();
        this.createZone();
    },
    watch: {
        'camera': function() {
            this.page('cameraPage').data();
            this.createZone();
        }
    },
    computed: {
        ...mapGetters(['getCamera']),
        title() {
            if (!this.camera) {
                return '';
            }
            return this.camera.name + ': settings';
        },
        camera() {
            return this.getCamera(this.$route.params.id) || null;
        },
        viewBox() {
            return '0 0 ' + this.camera.meta.width + ' ' + this.camera.meta.height;
        },
        enableClear() {
            return this.zone !== null && this.zone.get() != false;
        }
    },
    methods: {
        createZone() {
            setTimeout(() => {
                this.zone = new Zone(this.camera);
            }, 1); // FIXME!!!
        },
        clear() {
            this.zone.clearPoligon();
        },
        remove() {
            apiClient.removeCamera(this.camera.id).then(() => {
                this.$toast.success("Camera was removed successfully");
                this.removeDialog = false;
            }).catch(error => {
                var message = error.response && error.response.data ? error.response.data.message : error;
                this.$toast.error("Failed to remove camera: " + message);
                this.removeDialog = false;
            });
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