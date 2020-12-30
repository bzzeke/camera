const token = {

    remove() {
        window.localStorage.removeItem('authToken');
    },

    set(token) {
        window.localStorage.setItem('authToken', token);
    },

    isExist() {
        return window.localStorage.getItem('authToken') != null;
    },

    get() {
        return window.localStorage.getItem('authToken');
    }
}

export default token;