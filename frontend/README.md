# Frontend - React + Vite

This frontend project is built with modern web technologies to provide a fast, maintainable, and scalable user interface.

## Tech Stack

- **React**: A declarative, component-based JavaScript library for building user interfaces.
- **Vite**: A lightning-fast frontend build tool and development server, enabling instant HMR and optimized production builds.
- **Tailwind CSS**: A utility-first CSS framework for rapid UI development with a modern, responsive design.
- **ESLint**: A pluggable JavaScript linter to maintain code quality and consistency.
- **Prettier**: An opinionated code formatter for consistent layout across the project.

## Project Structure

```text
frontend/
├── public/              # Static assets (favicon, robots, sitemap)
├── script/              # Build helpers (e.g. sitemap generation)
├── src/
│   ├── assets/          # Images and static media
│   ├── components/      # UI components
│   ├── pages/           # Route pages
│   ├── router/          # React Router setup
│   ├── services/        # API client / service layer
│   ├── hooks/           # Shared React hooks
│   ├── contexts/        # React context providers
│   ├── i18n/            # Internationalization
│   ├── lib/             # Shared utilities
│   ├── config/          # Frontend config
│   ├── main.jsx         # App entry
│   └── index.css        # Global styles (Tailwind)
├── vite.config.js
├── eslint.config.js
├── prettier.config.js
└── package.json
```

## Lint & format

### Standards

| Item          | Value                                         |
| ------------- | --------------------------------------------- |
| Lint config   | [`eslint.config.js`](./eslint.config.js)      |
| Format config | [`prettier.config.js`](./prettier.config.js)  |
| Linter        | [ESLint](https://eslint.org/) 9 (flat config) |
| Formatter     | [Prettier](https://prettier.io/) 3            |
| Line length   | 100                                           |
| Indent        | 2 spaces                                      |
| Quotes        | Double quotes                                 |

### Manual commands

> Run from the `frontend/` directory. Requires `npm install` in this directory.

Lint the project; report issues without changing files:

```bash
npm run lint
```

Check formatting only; report mismatches without writing:

```bash
npm run format:check
```

Lint and auto-fix what ESLint can:

```bash
npm run lint:fix
```

Apply formatting to all supported files:

```bash
npm run format
```
