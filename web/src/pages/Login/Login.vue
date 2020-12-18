<template>
    <v-app>
        <v-container fluid>

        <v-row no-gutters v-show="authState == 'loading'">
            <v-col cols="12" class="main-part d-none d-md-none d-lg-flex">
            <div class="d-flex">
                <p>Camera server</p>
            </div>
            </v-col>
        </v-row>

        <v-row no-gutters v-show="authState != 'loading'">
            <v-col cols="7" class="main-part d-none d-md-none d-lg-flex">
            <div class="d-flex">
                <p>Camera server</p>
            </div>
            </v-col>
            <v-col cols="12" lg="5" class="login-part d-flex align-center justify-center">
            <v-row no-gutters>
                <v-col cols="12" class="login-part d-flex align-center justify-center flex-column">
                <div class="login-wrapper">

                    <v-form>
                    <v-container>
                        <v-row class="flex-column">
                        <v-col>
                            <p class="login-slogan display-2 text-center font-weight-medium my-10">{{ welcomeText }}</p>
                        </v-col>
                        <v-form>
                            <v-col>
                            <v-text-field
                                v-model="email"
                                :rules="emailRules"
                                label="Email Address"
                                required
                            ></v-text-field>
                            <v-text-field
                                v-model="password"
                                type="password"
                                label="Password"
                                required
                            ></v-text-field>

                            </v-col>
                            <v-col class="d-flex justify-space-between">
                            <v-btn
                                class="text-capitalize"
                                large
                                :disabled="password.length === 0 || email.length === 0"
                                color="primary"
                                @click="authorize"
                            >
                                {{ buttonText }}</v-btn>
                            </v-col>
                        </v-form>
                        </v-row>
                    </v-container>
                    </v-form>
                </div>
                </v-col>
            </v-row>
            </v-col>
        </v-row>
        </v-container>
    </v-app>
</template>

<script>

import apiClient from '../../api_client';

export default {
    name: 'Login',
    data() {
        return {
            authState: 'loading',
            email: '',
            password: '',

            emailRules: [
                v => !!v || 'E-mail is required',
                v => /.+@.+/.test(v) || 'E-mail must be valid',
            ],
            buttonText: '',
            welcomeText: ''
        }
    },
    methods: {

        authorize() {
            if (this.authState == 'signup') {
                this.signUp();
            } else {
                this.signIn();
            }
        },
        signIn(){
            apiClient.signIn(this.email, this.password).then(response => {
                    if (response.success) {
                        this.signInAndRedirect(response.results[0]);
                        return;
                    }

                    this.$toast.error("Failed to sign in: incorrect email or password");
                });

        },
        signUp(){
            apiClient.signUp(this.email, this.password).then(response => {
                    if (response.success) {
                        this.signInAndRedirect(response.results[0]);
                        return;
                    }

                    this.$toast.error("Failed to sign up: account is already created. Please sign in.");
                });

        },
        signInAndRedirect(token) {
            window.localStorage.setItem('authToken', token);
            this.$router.push('/dashboard');
        }

    },
    created() {

        apiClient.isNew().then(response => {

            if (response.success) {
                this.authState = 'signup';
                this.welcomeText = 'Please create account';
                this.buttonText = 'Sign up'
            } else {
                this.authState = 'signin';
                this.welcomeText = 'Please sign in';
                this.buttonText = 'Sign in'
            }
        });

        if (window.localStorage.getItem('authToken')) {
            this.$router.push('/dashboard');
        }
    }
  }




</script>

<style src="./Login.scss" lang="scss"/>
