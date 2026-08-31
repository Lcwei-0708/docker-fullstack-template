# Frontend - React + Vite

This frontend project is built with modern web technologies to provide a fast, maintainable, and scalable user interface.

## Tech Stack

- **React**: A declarative, component-based JavaScript library for building user interfaces.
- **Vite**: A lightning-fast frontend build tool and development server, enabling instant HMR and optimized production builds.
- **Tailwind CSS**: A utility-first CSS framework for rapid UI development with a modern, responsive design.
- **ESLint**: A pluggable JavaScript linter to maintain code quality and consistency.
- **Prettier**: An opinionated code formatter for consistent layout across the project.

## Features

- ⚡ Instant development startup and fast hot module replacement (HMR) with Vite
- 🎨 Modern, fully responsive UI styled with Tailwind CSS
- 🧩 Modular, component-based architecture using React
- 🛡️ Code quality enforced by ESLint
- ✨ Consistent formatting with Prettier

## Lint & format

### Standards

| Item           | Value                                         |
| -------------- | --------------------------------------------- |
| Lint config    | [`eslint.config.js`](./eslint.config.js)      |
| Format config  | [`prettier.config.js`](./prettier.config.js)  |
| Linter         | [ESLint](https://eslint.org/) 9 (flat config) |
| Formatter      | [Prettier](https://prettier.io/) 3            |
| Line length    | 100                                           |
| Indent         | 2 spaces                                      |
| Quotes         | Double quotes                                 |
| Semicolons     | Required                                      |
| Trailing comma | ES5 (objects, arrays, etc.)                   |

| Prettier option | Value   | Notes                                 |
| --------------- | ------- | ------------------------------------- |
| `semi`          | `true`  | Statements end with semicolons        |
| `singleQuote`   | `false` | Double quotes for strings             |
| `tabWidth`      | `2`     | 2 spaces per indent level             |
| `trailingComma` | `"es5"` | Trailing commas where valid in ES5    |
| `printWidth`    | `100`   | Wrap lines longer than 100 characters |

| Rule / plugin                           | Level        | Notes                                             |
| --------------------------------------- | ------------ | ------------------------------------------------- |
| `@eslint/js` recommended                | error / warn | Base JavaScript rules                             |
| `eslint-plugin-react-hooks` recommended | error / warn | Hooks usage                                       |
| `react-refresh/only-export-components`  | warn         | Vite fast refresh                                 |
| `no-unused-vars`                        | error        | See ignore patterns below                         |
| `eslint-config-prettier`                | —            | Disables ESLint rules that conflict with Prettier |

| `no-unused-vars` ignore | Pattern               | Reason                                 |
| ----------------------- | --------------------- | -------------------------------------- |
| Variables               | `^[A-Z_]`, `^motion$` | React components; Motion JSX namespace |
| Arguments               | `^_`, `^[A-Z]`        | Intentionally unused; component props  |
| Caught errors           | `^_`                  | Ignored catch bindings                 |

| Paths                                                        | Globals |
| ------------------------------------------------------------ | ------- |
| `src/**/*.{js,jsx}`                                          | Browser |
| `vite.config.js`, `script/**/*.js`, `src/config/env.node.js` | Node    |

### Manual commands

> Run from the `frontend/` directory. Requires `npm install` in this directory.

Lint the project; report issues without changing files:

```bash
npm run lint
```

Lint and auto-fix what ESLint can:

```bash
npm run lint:fix
```

Check formatting only; report mismatches without writing:

```bash
npm run format:check
```

Apply formatting to all supported files:

```bash
npm run format
```

Format first, then lint-fix when cleaning up:

```bash
npm run fix
```

Or step by step:

```bash
npm run format && npm run lint:fix
```
