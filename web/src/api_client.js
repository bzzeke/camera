import axios from 'axios';

const client = axios.create({
    baseURL: window.location.protocol + '//' + window.location.host,
    // baseURL: "http://10.10.10.179:9000",
    headers: {
        "Content-Type": "application/json",
    }
});

const getAuthToken = () => localStorage.getItem('authToken'); // FIXME

const authInterceptor = (config) => {
    config.headers['Authorization'] = getAuthToken();
    return config;
}

client.interceptors.request.use(authInterceptor);


class APIClient {

    getCameras() {
        return client.get('/camera/list')
            .then(response => Promise.resolve(response.data))
            .catch(error => Promise.reject(error));
    }

    signIn(username, password) {
        return client.post('/auth/signin', {
            username: username,
            password: password
        })
            .then(response => Promise.resolve(response.data))
            .catch(error => Promise.reject(error));
    }

    signUp(username, password) {
        return client.post('/auth/signup', {
            username: username,
            password: password
        })
            .then(response => Promise.resolve(response.data))
            .catch(error => Promise.reject(error));
    }

    saveZone(camera, data) {
        return client.post('/camera/' + camera + '/detection-zone', data)
            .then(response => Promise.resolve(response.data))
            .catch(error => Promise.reject(error));
    }

    isNew() {
        return client.get('/auth/is-new')
            .then(response => Promise.resolve(response.data))
            .catch(error => Promise.reject(error));
    }

    discovery() {
        return client.get('/discovery')
            .then(response => Promise.resolve(response.data))
            .catch(error => Promise.reject(error));
    }
}

const apiClient = new APIClient();

export default apiClient;

