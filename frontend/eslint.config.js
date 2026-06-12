import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import tseslint from 'typescript-eslint'
import react from 'eslint-plugin-react'
import jsxA11y from 'eslint-plugin-jsx-a11y'
import importPlugin from 'eslint-plugin-import'
import simpleImportSort from 'eslint-plugin-simple-import-sort'
import prettier from 'eslint-config-prettier'

export default [
  { ignores: ['dist', 'build', 'src/api/generated'] },
  {
    files: ['**/*.{ts,tsx}'],
    ...js.configs.recommended,
  },
  ...tseslint.configs.recommended,
  {
    files: ['**/*.{ts,tsx}'],
    ...react.configs.flat.recommended,
    ...react.configs.flat['jsx-runtime'],
    languageOptions: {
      ...react.configs.flat.recommended.languageOptions,
      ecmaVersion: 2020,
      globals: globals.browser,
    },
    settings: {
      react: {
        version: 'detect',
      },
    },
  },
  {
    files: ['**/*.{ts,tsx}'],
    plugins: {
      'react-hooks': reactHooks,
    },
    rules: {
      ...reactHooks.configs.recommended.rules,
    },
  },
  {
    files: ['**/*.{ts,tsx}'],
    ...jsxA11y.flatConfigs.recommended,
  },
  {
    files: ['**/*.{ts,tsx}'],
    plugins: {
      'simple-import-sort': simpleImportSort,
      import: importPlugin,
      'react-refresh': reactRefresh,
    },
    rules: {
      'react-refresh/only-export-components': [
        'warn',
        { allowConstantExport: true },
      ],
      'simple-import-sort/imports': 'error',
      'simple-import-sort/exports': 'error',
      'import/first': 'error',
      'import/newline-after-import': 'error',
      'import/no-duplicates': 'error',
      // F4K uses semantic breakpoints only (tablet: 500px, desktop: 1024px),
      // defined in src/index.css. Tailwind's sm/md/lg/xl/2xl are removed from
      // the theme, so these variants silently compile to nothing — ban them.
      // (Watch out when copying in shadcn components: replace md:/lg: with
      // tablet:/desktop:.)
      'no-restricted-syntax': [
        'error',
        {
          selector:
            'Literal[value=/(^|[^a-zA-Z0-9-])(sm|md|lg|xl|2xl):[a-z]/]',
          message:
            'Tailwind default breakpoints (sm/md/lg/xl/2xl) are not defined in this project and compile to nothing. Use the F4K semantic breakpoints: tablet: (500px) or desktop: (1024px).',
        },
        {
          selector:
            'TemplateElement[value.raw=/(^|[^a-zA-Z0-9-])(sm|md|lg|xl|2xl):[a-z]/]',
          message:
            'Tailwind default breakpoints (sm/md/lg/xl/2xl) are not defined in this project and compile to nothing. Use the F4K semantic breakpoints: tablet: (500px) or desktop: (1024px).',
        },
      ],
    },
  },
  prettier, // Must be last
]