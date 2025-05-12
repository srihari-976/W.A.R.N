module.exports = {
  webpack: {
    configure: (webpackConfig) => {
      // Update the entry point to use index.jsx
      webpackConfig.entry = './src/index.jsx';
      return webpackConfig;
    },
  },
}; 