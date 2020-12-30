import Vue from 'vue';
import Vuex from 'vuex';
import apiClient from '@/services/api_client';

Vue.use(Vuex);

const store = new Vuex.Store({

    namespace: true,
    state: {
        drawer: true,
        authToken: null,
        cameras: []
    },
    mutations: {
        toggleDrawer(state) {
            state.drawer = !state.drawer;
        },
        setCameras(state, cameras) {
            state.cameras = cameras;
        },
        addCamera(state, cameras) {
            state.cameras.push(cameras[0]); // FIXME
        },
        removeCamera(state, id) {
            state.cameras = state.cameras.filter(item => item.id != id);
        },
        setAuthToken(state, newToken) {
            state.authToken = newToken;
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
        },
        getAuthToken: (state) => {
            return state.authToken;
        }
    }
});

store.watch((state) => state.authToken, (newValue) => {
    if (newValue != "") {
        apiClient.getCameras().then(response => {
            store.commit('setCameras', response.results);
        });
    }
});

export default store;