import axios from 'axios';
import token from '@/services/token';

const client = axios.create({
    baseURL: window.location.protocol + '//' + window.location.host,
    headers: {
        "Content-Type": "application/json",
    }
});

const authInterceptor = (config) => {
    config.headers['Authorization'] = token.get();
    return config;
}

client.interceptors.request.use(authInterceptor);


class APIClient {

    getCameras() {
        return client.get('/camera')
            .then(response => Promise.resolve(response.data))
            .catch(error => Promise.reject(error));

    }

    getClips(filters) {
        return client.get('/clips', {
            params: {
                date: filters.date.replaceAll('-', ''),
                camera: filters.camera,
                category: filters.category
            }
        })
            .then(response => Promise.resolve(response.data))
            .catch(error => Promise.reject(error));
    }

    addCamera(camera) {
        return client.post('/camera', camera)
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

    saveOptions(camera, data) {
        return client.post('/camera/' + camera, data)
            .then(response => Promise.resolve(response.data))
            .catch(error => Promise.reject(error));
    }

    removeCamera(camera) {
        return client.delete('/camera/' + camera)
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

    settings() {
        return client.get('/settings')
            .then(response => Promise.resolve(response.data))
            .catch(error => Promise.reject(error));
    }

    saveSettings(settings) {
        return client.post('/settings', settings)
            .then(response => Promise.resolve(response.data))
            .catch(error => Promise.reject(error));
    }

    homekit() {
        return client.get('/camera/homekit')
        .then(response => Promise.resolve(response.data))
        .catch(error => Promise.reject(error));
    }
}

const apiClient = new APIClient();

export default apiClient;

