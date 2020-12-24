import Vue from 'vue';
import Vuex from 'vuex';

Vue.use(Vuex);

export default new Vuex.Store({

    namespace: true,
    state: {
        drawer: true,
        cameras: []
    },
    mutations: {
        toggleDrawer(state) {
            state.drawer = !state.drawer;
        },
        setCameras(state, cameras) {
            state.cameras = cameras;
        }
    },
    actions: {
        TOGGLE_DRAWER({ commit }) {
            commit('toggleDrawer');
        }
    },
    getters: {
        DRAWER_STATE(state) {
            return state.drawer;
        },
        getCamera: (state) => (id) => {
            return state.cameras.find(camera => camera.id === id);
        },
        getCameras: (state) => {
            return state.cameras;
        }
    }
});
