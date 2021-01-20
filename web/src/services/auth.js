import token from "./token";
import apiClient from "./api_client";

const auth = {
    signIn(email, password) {
        return apiClient.signIn(email, password).then(response => {
            if (response.success) {
                token.set(response.results[0])
            }
            return Promise.resolve(response)
        }).catch(error => Promise.reject(error));
    },

    signUp(email, password) {
        return apiClient.signUp(email, password).then(response => {
            if (response.success) {
                token.set(response.results[0])
            }
            return Promise.resolve(response)
        }).catch(error => Promise.reject(error));
    },

    signOut() {
        token.remove()
    },

    isAuthenticated() {
        return token.isExist();
    }
}

export default auth;