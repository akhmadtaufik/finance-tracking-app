/* eslint-env node */
module.exports = {
  root: true,
  extends: [
    'plugin:vue/vue3-recommended',
    'plugin:vuejs-accessibility/recommended',
    'eslint:recommended',
    '@vue/eslint-config-prettier'
  ],
  plugins: ['vuejs-accessibility'],
  parserOptions: {
    ecmaVersion: 'latest',
    sourceType: 'module'
  },
  env: {
    browser: true,
    node: true,
    es2022: true
  },
  rules: {
    'vue/multi-word-component-names': 'off',
    'vue/require-default-prop': 'off',
    'no-unused-vars': ['error', { argsIgnorePattern: '^_' }]
  }
}
