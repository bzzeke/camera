import axios from 'axios';

const apiClient = axios.create({
    baseURL: "http://172.25.33.41:9000",
    headers: {
        "Content-Type": "application/json",
    }
});

/*const getAuthToken = () => localStorage.getItem('vue-authenticate.vueauth_token'); // FIXME

const authInterceptor = (config) => {
    config.headers['BTOKEN'] = getAuthToken();
    return config;
}

apiClient.interceptors.request.use(authInterceptor);
*/
export default apiClient;