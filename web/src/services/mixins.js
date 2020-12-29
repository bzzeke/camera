var mixins = {
    data() {
        return {
            categoryIcons: {
                person: "🚶🏻‍♂️",
                car: "🚗",
                bus: "🚌 ",
                truck: "🚚",
                motorcycle: "🏍",
                bicycle: "🚲 "
            }
        }
    },
    methods: {
        getCategories(withAll = true) {
            let categories = [
                {
                    "text": "Person",
                    "value": "person"
                },
                {
                    "text": "Car",
                    "value": "car"
                },
                {
                    "text": "Bus",
                    "value": "bus"
                },
                {
                    "text": "Truck",
                    "value": "truck"
                },
                {
                    "text": "Motorcycle",
                    "value": "motorcycle"
                },
                {
                    "text": "Bicycle",
                    "value": "bicycle"
                },
            ];

            if (withAll) {
                categories.unshift({
                    "text": "All categories",
                    "value": ""
                });
            }

            return categories;
        },
        page(name) {
            if (this.$refs[name]) {
                return this.$refs[name];
            }

            return {
                dataOrEmpty() {
                },
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