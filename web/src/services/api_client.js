import axios from 'axios';

const client = axios.create({
    // baseURL: window.location.protocol + '//' + window.location.host,
    baseURL: "http://10.100.1.6:9000",
    headers: {
        "Content-Type": "application/json",
    }
});

const request = axios.CancelToken.source();

const getAuthToken = () => localStorage.getItem('authToken'); // FIXME

const authInterceptor = (config) => {
    config.headers['Authorization'] = getAuthToken();
    return config;
}

client.interceptors.request.use(authInterceptor);


class APIClient {

    getCameras() {
        return Promise.resolve({
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
        });
        // return client.get('/camera/list', { cancelToken: request.token })
        //     .then(response => Promise.resolve(response.data))
        //                 .catch(error => {
        //     if (client.isCancel(error)) {
        //         return;
        //     }
        //     Promise.reject(error)
        // });
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
        return client.get('/clips/list', {
            cancelToken: request.token,
            params: {
                date: filters.date.replaceAll('-', ''),
                camera: filters.camera,
                category: filters.category
            }
        })
            .then(response => Promise.resolve(response.data))
            .catch(error => {
                if (client.isCancel(error)) {
                    console.log('cancel');
                    return;
                }
                Promise.reject(error)
            });
    }

    addCamera(camera) {
        return client.post('/camera/add', camera)
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
        return client.post('/camera/' + camera + '/options', data)
            .then(response => Promise.resolve(response.data))
            .catch(error => Promise.reject(error));
    }

    removeCamera(camera) {
        return client.delete('/camera/' + camera)
            .then(response => Promise.resolve(response.data))
            .catch(error => Promise.reject(error));
    }

    isNew() {
        return client.get('/auth/is-new', { cancelToken: request.token })
            .then(response => Promise.resolve(response.data))
            .catch(error => {
                if (client.isCancel(error)) {
                    return;
                }
                Promise.reject(error)
            });
    }

    discovery() {
        return client.get('/discovery', { cancelToken: request.token })
            .then(response => Promise.resolve(response.data))
            .catch(error => {
                if (client.isCancel(error)) {
                    return;
                }
                Promise.reject(error)
            });
    }

    cancel() {
        request.cancel();
    }
}

const apiClient = new APIClient();

export default apiClient;

