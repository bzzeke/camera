var mixins = {
    data() {
        return {
        }
    },
    methods: {
        page(name) {
            if (this.$refs[name]) {
                return this.$refs[name];
            }

            return {
                data() {
                },
                empty() {
                },
                error() {
                }
            }
        }
    }
}

export default mixins;