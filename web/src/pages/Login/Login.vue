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
                                v-on:keyup.enter="!buttonDisabled ? authorize() : null"
                            ></v-text-field>

                            </v-col>
                            <v-col class="d-flex justify-space-between">
                            <v-btn
                                class="text-capitalize"
                                large
                                :disabled="buttonDisabled"
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

import apiClient from '@/services/api_client';
import auth from '@/services/auth';

export default {
    name: 'Login',
    data() {
        return {
            authState: 'loading',
            email: '',
            password: '',
            requesting: false,
            emailRules: [
                v => !!v || 'E-mail is required',
                v => /.+@.+/.test(v) || 'E-mail must be valid',
            ],
            buttonText: '',
            welcomeText: ''
        }
    },
    computed: {
        buttonDisabled() {
            return this.password.length === 0 || this.email.length === 0 || this.requesting;
        }
    },
    methods: {

        authorize() {
            this.requesting = true;
            if (this.authState == 'signup') {
                this.signUp();
            } else {
                this.signIn();
            }
        },
        signIn(){
            auth.signIn(this.email, this.password)
                .then(response => {
                    if (response.success) {
                        this.$router.push('/dashboard');
                        return;
                    }

                    this.$toast.error("Failed to sign in: incorrect email or password");
                    this.requesting = false;
                })
                .catch(error => {
                    var message = error.response && error.response.data ? error.response.data.message : error;
                    this.$toast.error("Failed to sign in: " + message);
                    this.requesting = false;
                });
        },
        signUp(){
            auth.signUp(this.email, this.password)
                .then(response => {
                    if (response.success) {
                        this.$router.push('/dashboard');
                        return;
                    }

                    this.$toast.error("Failed to sign up: account is already created. Please sign in.");
                    this.requesting = false;
                })
                .catch(error => {
                    var message = error.response && error.response.data ? error.response.data.message : error;
                    this.$toast.error("Failed to sign up: " + message);
                    this.requesting = false;
                });
        }
    },
    created() {

        apiClient.isNew()
            .then(response => {
                if (response.success) {
                    this.authState = 'signup';
                    this.welcomeText = 'Please create account';
                    this.buttonText = 'Sign up'
                } else {
                    this.authState = 'signin';
                    this.welcomeText = 'Please sign in';
                    this.buttonText = 'Sign in'
                }
            })
            .catch(error => {
                var message = error.response && error.response.data ? error.response.data.message : error;
                this.$toast.error("Failed to get account info: " + message);
            });

        if (auth.isAuthenticated()) {
            this.$router.push('/dashboard');
        }
    }
  }




</script>

<style src="./Login.scss" lang="scss"/>
