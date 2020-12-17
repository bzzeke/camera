import axios from 'axios';

const client = axios.create({
    baseURL: window.location.protocol + '//' + window.location.host,
    // baseURL: "http://10.10.10.180:8000",
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
        return client.get('/cameras')
            .then(response => Promise.resolve(response.data))
            .catch(error => Promise.reject(error));
    }

    signIn(username, password) {
        return client.post('/signin', {
            username: username,
            password: password
        })
            .then(response => Promise.resolve(response.data))
            .catch(error => Promise.reject(error));
    }

    signUp(username, password) {
        return client.post('/signup', {
            username: username,
            password: password
        })
            .then(response => Promise.resolve(response.data))
            .catch(error => Promise.reject(error));
    }

    saveZone(camera, data) {
        return client.post('/detection-zone/' + camera, data)
            .then(response => Promise.resolve(response.data))
            .catch(error => Promise.reject(error));
    }
}

const apiClient = new APIClient();

export default apiClient;

