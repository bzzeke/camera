module.exports = {
    "transpileDependencies": [
        "vuetify"
    ],
    publicPath: '/camera-server/',
    chainWebpack: config => {
        config
            .plugin('html')
            .tap(args => {
                args[0].title = 'Camera server'
                return args
            })
    }
}
