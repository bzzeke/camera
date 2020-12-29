<template>

    <div class="md-empty-state">
        <div class="md-empty-state-container">
            <v-icon size="160">{{ mdIcon }}</v-icon>
            <strong class="md-empty-state-label" v-if="mdLabel">{{ mdLabel }}</strong>
            <p class="md-empty-state-description" v-if="emptyMessage">{{ emptyMessage }}</p>
            <slot />
        </div>
    </div>

</template>

<script>
export default {
    name: 'EmptyState',
    props: ['emptyMessage'],
    data() {
        return {
            mdIcon: "mdi-flask-empty-outline",
            mdLabel: "Nothing to display"
        };
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