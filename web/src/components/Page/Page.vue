<template>
    <v-container fluid>
        <v-row no-gutters class="d-flex justify-space-between mt-10 mb-6">
            <h1 class="page-title">{{ title }}</h1>

            <slot name="buttons"></slot>
        </v-row>

        <slot name="toolbar"></slot>

        <v-row v-if="dataState == 'error'">
            <v-col cols="12" md="12">
                <ErrorState :errorMessage="errorMessage" />
            </v-col>
        </v-row>

        <v-row v-if="dataState == 'empty'">
            <v-col cols="12" md="12">
                <EmptyState :emptyMessage="emptyMessage" />
            </v-col>
        </v-row>

        <v-row v-if="dataState == 'loading'">
            <slot name="loading"></slot>
        </v-row>

        <v-row v-if="dataState == 'data'">
            <slot name="data"></slot>
        </v-row>

    </v-container>
</template>

<script>
import ErrorState from '@/components/Page/ErrorState';
import EmptyState from '@/components/Page/EmptyState';

export default {
    name: 'Page',
    components: { ErrorState, EmptyState },
    props: ['title'],
    data() {
        return {
            errorMessage: "",
            emptyMessage: "",
            dataState: "loading"
        };
    },
    methods: {
        error(message) {
            this.dataState = 'error';
            this.errorMessage = message || '';
        },
        empty(message) {
            this.dataState = 'empty';
            this.emptyMessage = message || '';
        },
        data() {
            this.dataState = 'data';
        },
        dataOrEmpty(total) {
            if (total > 0) {
                this.data();
            } else {
                this.empty('');
            }
        }
    }
};
</script>

<style lang="scss">
    @mixin md-empty-state-base () {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
    }
    .md-empty-state {
        @include md-empty-state-base;
        max-width: 420px;
        padding: 36px;
        margin: 0 auto;
        position: relative;
        will-change: transform, opacity;
        &.md-rounded {
        max-width: auto;
        border-radius: 50%;
        .md-empty-state-container {
            padding: 40px;
            position: absolute;
            top: 0;
            right: 0;
            bottom: 0;
            left: 0;
        }
        }
        .md-button {
        margin: .5em 0 0;
        }
    }
    .md-empty-state-enter {
        opacity: 0;
        transform: scale(.87);
        .md-empty-state-container {
        opacity: 0;
        }
    }
    .md-empty-state-container {
        @include md-empty-state-base;
        will-change: opacity;
    }
    .md-empty-state-icon {
        /*@include md-icon-size(160px);*/
        margin: 0;
    }
    .md-empty-state-label {
        font-size: 26px;
        font-weight: 500;
        line-height: 40px;
    }
    .md-empty-state-description {
        margin: 1em 0;
        font-size: 16px;
        line-height: 24px;
    }
</style>