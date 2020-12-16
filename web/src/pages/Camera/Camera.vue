<template>
<v-container fluid>

    <v-row no-gutters class="d-flex justify-space-between mt-10 mb-6">
        <h1 class="page-title">Zone definition for {{ this.cameraName }}</h1>

        <div>
            <v-btn color="secondary" class="text-capitalize mr-2" @click="clear()">Clear</v-btn>
            <v-btn color="primary" class="text-capitalize" @click="save()">Save</v-btn>
        </div>

    </v-row>
    <v-row>
        <div class="img-overlay-wrap">
            <img :src="snapshotURL" :width="width" :height="height">
            <svg class="container_svg" :viewBox="viewBox"></svg>
        </div>
    </v-row>
</v-container>
</template>

<script>

import Zone from '../../logic/zone';
import { mapGetters } from 'vuex';

export default {
    name: 'Camera',
    data() {
        return {
            zone: null
        }
    },
    watch: {
        camera() {
            this.zone = new Zone(this.camera);
        }
    },
    computed: {
        ...mapGetters(['getCamera']),
        camera() {
            return this.getCamera(this.$route.params.name) || {};
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
        }
    },
    methods: {
        clear() {
            this.zone.clearPoligon();
        },
        save() {
            this.zone.savePoligon();
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