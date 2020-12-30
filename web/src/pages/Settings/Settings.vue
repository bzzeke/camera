<template>

    <Page ref="settingsPage" title="Settings">
        <template v-slot:buttons>
            <div>
                <v-btn color="primary" class="text-capitalize" @click="save()">Save</v-btn>
            </div>
        </template>

        <template v-slot:loading>

            <v-col cols="12">
            <v-card class="mx-1 mb-1">
                <v-card-text>
                    <div v-for="i in 4" :key="i">
                        <div :class="i > 1 ? 'mt-10' : ''">
                            <v-skeleton-loader class="mx-auto pa-3" type="heading"></v-skeleton-loader>
                            <v-skeleton-loader class="mx-auto pa-3" type="text@4"></v-skeleton-loader>
                        </div>
                    </div>
                </v-card-text>
            </v-card>
            </v-col>
        </template>

        <template v-slot:data>
            <v-col cols="12">
            <v-card class="mx-1 mb-1">
                <v-card-text>
                    <v-row>
                        <v-col cols="6">
                            <div v-for="(option, index) in settings" :key="option.name">
                                <v-row v-if="option.type == 'header'">
                                    <v-col>
                                        <h3 :class="index > 0 ? 'mt-10' : ''">{{ option.title }}</h3>
                                    </v-col>
                                </v-row>
                                <v-row v-if="option.type == 'checkbox'">
                                    <v-col>
                                        <v-checkbox v-model="option.value" :label="option.title"></v-checkbox>
                                    </v-col>
                                </v-row>
                                <v-row v-if="option.type == 'select'">
                                    <v-col>
                                        <v-select v-model="option.value" :items="option.items" :label="option.title">
                                        </v-select>
                                    </v-col>
                                </v-row>
                                <v-row v-if="option.type == 'input'">
                                    <v-col>
                                        <v-text-field v-model="option.value" :label="option.title" hide-details="auto"></v-text-field>
                                    </v-col>
                                </v-row>
                            </div>
                        </v-col>
                        <v-col cols="6" class="text-center" v-if="homekit">
                            <VueQrcode :value="homekit.xhm_uri" :options="{width: 400}" />
                            <p>
                                Scan QR code to add Camera Bridge to your Apple Home or enter pincode manually:
                            </p>
                            <h4>{{ homekit.pincode }}</h4>
                        </v-col>
                    </v-row>
                </v-card-text>
            </v-card>
            </v-col>
        </template>

    </Page>

</template>

<script>

import apiClient from '@/services/api_client';
import mixins from '@/services/mixins';

import Page from '@/components/Page/Page';

import VueQrcode from '@chenfengyuan/vue-qrcode';

export default {
    name: 'Settings',
    mixins: [mixins],
    components: { Page, VueQrcode },
    data() {
        return {
            settings: [],
            homekit: null
        }
    },
    mounted() {
        apiClient.settings().then(response => {
            this.settings = response.results;
            this.page('settingsPage').dataOrEmpty(this.settings.length);
        }).catch(error => {
            var message = error.response && error.response.data ? error.response.data.message : error;
            this.page('settingsPage').error(message);
        });

        apiClient.homekit().then(response => {
            this.homekit = response.results[0];
        });
    },
    methods: {

        save() {
            let settings = this.settings
                .filter(item => item.name ? true : false)
                .map(item => {
                    return {
                        name: item.name,
                        value: item.value
                    }
                });

            apiClient.saveSettings(settings).then(() => {
                this.$toast.success("Settings were successfully updated");
            }).catch(error => {
                var message = error.response && error.response.data ? error.response.data.message : error;
                this.$toast.error("Failed to update settings: " + message);
            });

        }
    }
};
</script>
