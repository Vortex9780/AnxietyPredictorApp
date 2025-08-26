// babel.config.js
module.exports = function(api) {
  api.cache(true);

  return {
    presets: [
      // Expo’s default preset (includes React Native transforms)
      'babel-preset-expo',

      // If you have any Flow‐annotated code in node_modules (e.g. expo internals):
      '@babel/preset-flow',

      // If you’re writing TS in your app/ folder:
      '@babel/preset-typescript',
    ],
    plugins: [
      // expo-router’s hook into Metro (still required on SDK <= 53):
      'expo-router/babel',

      // If you’re using react-native-reanimated:
      'react-native-reanimated/plugin',

      // Enable Flow syntax parsing (just in case):
      ['@babel/plugin-syntax-flow', { all: true }],
    ],
  };
};