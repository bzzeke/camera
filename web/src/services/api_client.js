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
        return client.get('/api/camera')
            .then(response => Promise.resolve(response.data))
            .catch(error => Promise.reject(error));

    }

    getClips(filters) {
        return client.get('/api/clips', {
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
        return client.post('/api/camera', camera)
            .then(response => Promise.resolve(response.data))
            .catch(error => Promise.reject(error));
    }

    signIn(username, password) {
        return client.post('/api/auth/signin', {
            username: username,
            password: password
        })
            .then(response => Promise.resolve(response.data))
            .catch(error => Promise.reject(error));
    }

    signUp(username, password) {
        return client.post('/api/auth/signup', {
            username: username,
            password: password
        })
            .then(response => Promise.resolve(response.data))
            .catch(error => Promise.reject(error));
    }

    saveOptions(camera, data) {
        return client.post('/api/camera/' + camera, data)
            .then(response => Promise.resolve(response.data))
            .catch(error => Promise.reject(error));
    }

    removeCamera(camera) {
        return client.delete('/api/camera/' + camera)
            .then(response => Promise.resolve(response.data))
            .catch(error => Promise.reject(error));
    }

    isNew() {
        return client.get('/api/auth/is-new')
            .then(response => Promise.resolve(response.data))
            .catch(error => Promise.reject(error));
    }

    discovery() {
        return client.get('/api/discovery')
            .then(response => Promise.resolve(response.data))
            .catch(error => Promise.reject(error));
    }

    settings() {
        return client.get('/api/settings')
            .then(response => Promise.resolve(response.data))
            .catch(error => Promise.reject(error));
    }

    saveSettings(settings) {
        return client.post('/api/settings', settings)
            .then(response => Promise.resolve(response.data))
            .catch(error => Promise.reject(error));
    }

    homekit() {
        return client.get('/api/camera/homekit')
        .then(response => Promise.resolve(response.data))
        .catch(error => Promise.reject(error));
    }
}

const apiClient = new APIClient();

export default apiClient;

