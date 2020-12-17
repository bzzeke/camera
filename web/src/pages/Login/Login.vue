<template>
    <v-app>
        <v-container fluid>
        <v-row no-gutters>
            <v-col cols="7" class="main-part d-none d-md-none d-lg-flex">
            <div class="d-flex">
                <p>Camera server</p>
            </div>
            </v-col>
            <v-col cols="12" lg="5" class="login-part d-flex align-center justify-center">
            <v-row no-gutters>
                <v-col cols="12" class="login-part d-flex align-center justify-center flex-column">
                <div class="login-wrapper">
                    <v-tabs grow>
                    <v-tabs-slider></v-tabs-slider>
                    <v-tab :href="`#tab-login`">
                        LOGIN
                    </v-tab>
                    <v-tab :href="`#tab-newUser`">
                        New User
                    </v-tab>

                    <v-tab-item :value="'tab-login'" >
                        <v-form>
                        <v-container>
                            <v-row class="flex-column">
                            <v-col>
                                <p class="login-slogan display-2 text-center font-weight-medium my-10">Good Morning, User</p>
                            </v-col>
                            <v-form>
                                <v-col>
                                <v-text-field
                                    v-model="email"
                                    :rules="emailRules"
                                    value="admin@example.com"
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
                                    @click="signIn"
                                >
                                    Login</v-btn>
                                <v-btn large text class="text-capitalize primary--text">Forget Password</v-btn>
                                </v-col>
                            </v-form>
                            </v-row>
                        </v-container>
                        </v-form>
                    </v-tab-item>

                    <v-tab-item :value="'tab-newUser'" >
                        <v-form>
                        <v-container>
                            <v-row class="flex-column">

                            <v-col>
                                <p class="login-slogan display-2 text-center font-weight-medium mt-10">Welcome!</p>
                                <p class="login-slogan display-1 text-center font-weight-medium mb-10">Create your account</p>
                            </v-col>

                            <v-form>
                                <v-col>
                                <v-text-field
                                    v-model="createEmail"
                                    :rules="emailRules"
                                    label="Email Address"
                                    required
                                ></v-text-field>
                                <v-text-field
                                    v-model="createPassword"
                                    :rules="passRules"
                                    type="password"
                                    label="Password"
                                    hint="At least 6 characters"
                                    required
                                ></v-text-field>
                                </v-col>
                                <v-col class="d-flex justify-space-between">
                                <v-btn
                                    large
                                    block
                                    :disabled="createEmail.length === 0 || createPassword === 0"
                                    color="primary"
                                    @click="signUp"
                                >
                                    Create your account</v-btn>
                                </v-col>
                            </v-form>

                            <v-col cols="12" class="d-flex align-center my-4">
                                <v-divider></v-divider>
                                <span class="px-5"> or </span>
                                <v-divider></v-divider>
                            </v-col>
                            </v-row>
                        </v-container>
                        </v-form>
                    </v-tab-item>

                    </v-tabs>
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
            email: '',
            password: '',
            createEmail: '',
            createPassword: '',

            emailRules: [
                v => !!v || 'E-mail is required',
                v => /.+@.+/.test(v) || 'E-mail must be valid',
            ],
            passRules: [
                v => !!v || 'Password is required',
                v => v.length >= 6 || 'Min 6 characters'
            ]
        }
    },
    methods: {
        signIn(){
            apiClient.signIn(this.email, this.password).then(response => {
                    if (response.success) {
                        this.signInAndRedirect(response.results[0]);
                        return;
                    }
                    // show notification
                    console.log(response);
                });

        },
        signUp(){
            apiClient.signUp(this.email, this.password).then(response => {
                    if (response.success) {
                        this.signInAndRedirect(response.results[0]);
                        return;
                    }
                    // show notification
                    console.log(response);
                });

        },
        signInAndRedirect(token) {
            window.localStorage.setItem('authToken', token);
            this.$router.push('/dashboard');
        }

    },
    created() {
        if (window.localStorage.getItem('authToken')) {
            this.$router.push('/dashboard');
        }
    }
  }




</script>

<style src="./Login.scss" lang="scss"/>
