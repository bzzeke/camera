import axios from 'axios';
import token from '@/services/token';

const client = axios.create({
    // baseURL: window.location.protocol + '//' + window.location.host,
    baseURL: "http://10.100.1.6:9000",
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
        /*return Promise.resolve({
            "results": [
                {
                    "name": "Test",
                    "id": "id",
                    "manage_url": "http://localhost",
                    "meta": {
                        "width": 1600,
                        "height": 900
                    },
                    "detection": {
                        "enabled": false,
                        "zone":[],
                        "valid_categories": []
                    }
                },
                {
                    "name": "Test2",
                    "id": "id2",
                    "manage_url": "http://localhost3",
                    "meta": {
                        "width": 1600,
                        "height": 900
                    },
                    "detection": {
                        "enabled": false,
                        "zone":[],
                        "valid_categories": []
                    }
                }
            ]
        });*/
        return client.get('/camera')
            .then(response => Promise.resolve(response.data))
            .catch(error => Promise.reject(error));

    }

    getClips(filters) {
        /*return Promise.resolve({
            "results": [
                {
                    "timestamp": 1608110809,
                    "video_url": "http://localhost",
                    "thumbnail_url": "http://localhost",
                    "camera": "Test",
                    "objects": ["person"]
                },
                {
                    "timestamp": 1608110109,
                    "video_url": "http://localhost",
                    "thumbnail_url": "http://localhost",
                    "camera": "Test",
                    "objects": ["person"]
                },
                {
                    "timestamp": 1608119009,
                    "video_url": "http://localhost",
                    "thumbnail_url": "http://localhost",
                    "camera": "Test",
                    "objects": ["person", "car"]
                },
                {
                    "timestamp": 1608119709,
                    "video_url": "http://localhost",
                    "thumbnail_url": "http://localhost",
                    "camera": "Test",
                    "objects": ["car"]
                }
            ]
        });*/
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
        /*return Promise.resolve({
            "results": [
                {
                    "title": "Capturer",
                    "type": "header",
                },
                {
                    "name": "capturer_type",
                    "title": "Type",
                    "type": "select",
                    "value": "ffmpeg",
                    "items": [
                        {"text": "FFMPEG", "value": "ffmpeg"},
                        {"text": "GStreamer", "value": "gstreamer"}
                    ]
                },
                {
                    "name": "capturer_hardware",
                    "title": "Hardware",
                    "type": "select",
                    "value": "gpu",
                    "items": [
                        {"text": "CPU", "value": "cpu"},
                        {"text": "GPU", "value": "gpu"}
                    ]
                },
                {
                    "title": "Notifications",
                    "type": "header",
                },
                {
                    "name": "notifications_enable",
                    "title": "Enable",
                    "value": true,
                    "type": "checkbox",
                },
                {
                    "name": "notifications_url",
                    "title": "Notify URL",
                    "value": "http://localhost/a/b/x",
                    "type": "input",
                },
                {
                    "title": "Detector",
                    "type": "header",
                },
                {
                    "name": "detector_clips_max_size",
                    "title": "Clips max size",
                    "value": "100",
                    "type": "input",
                },
                {
                    "name": "detector_model_path",
                    "title": "Model path",
                    "value": "/srv/home/models",
                    "type": "input",
                },
                {
                    "name": "detector_hardware",
                    "title": "Hardware",
                    "type": "select",
                    "value": "cpu",
                    "items": [
                        {"text": "CPU", "value": "cpu"},
                        {"text": "GPU", "value": "gpu"}
                    ]
                },
            ]
        });*/
        return client.get('/settings')
            .then(response => Promise.resolve(response.data))
            .catch(error => Promise.reject(error));
    }

    saveSettings(settings) {
        return client.post('/settings', settings)
            .then(response => Promise.resolve(response.data))
            .catch(error => Promise.reject(error));
    }
}

const apiClient = new APIClient();

export default apiClient;

