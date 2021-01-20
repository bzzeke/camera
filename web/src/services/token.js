import store from '@/store/index';

const token = {

    remove() {
        window.localStorage.removeItem('authToken');
        store.commit('setAuthToken', "");
    },

    set(token) {
        window.localStorage.setItem('authToken', token);
        store.commit('setAuthToken', token);
    },

    isExist() {
        return window.localStorage.getItem('authToken') != null;
    },

    get() {
        return window.localStorage.getItem('authToken');
    }
}

store.commit('setAuthToken', token.get());

export default token;