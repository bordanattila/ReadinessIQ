# ReadinessIQ frontend

Vite + React + TypeScript UI for the ReadinessIQ platform. See the repo root **`README.md`** for full stack setup.

### Features

- **Routing** (`react-router-dom`): `/` overview, `/sites`, `/parts`, `/suppliers` full rankings.
- **Root cause summary** — horizontal bar chart (percent share of total risk signals).
- **Top 5 dashboard** — cards with “View all” → shared **`ViewAll`** full-width table (`viewAll.tsx`) and extended columns in **`riskRankingViewModel.ts`**.

### Scripts

| Command        | Description                |
| -------------- | -------------------------- |
| `npm run dev`  | Vite dev server (:5173)    |
| `npm run build`| Typecheck + production build |
| `npm run test` | Vitest + Testing Library   |
| `npm run lint` | ESLint                     |

### Tests (Vitest)

| File | Coverage |
|------|----------|
| `src/api.test.ts` | REST client helpers |
| `src/App.test.tsx` | Shell, overview, `/sites` view-all route |
| `src/components/top5card.test.tsx` | Card states, cells, View all link |
| `src/components/top5dashboard.test.tsx` | Parallel API load + errors |
| `src/components/viewAll.test.tsx` | Full-list template table, back link |
| `src/components/sidebar.test.tsx` | Nav links |
| `src/components/rootCauseSummaryChart.test.tsx` | Summary chart + percentages |
| `src/pages/RankingViewAllPage.test.tsx` | Sites full ranking + mapped columns |

---

# React + TypeScript + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Oxc](https://oxc.rs)
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/)

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the ESLint configuration

If you are developing a production application, we recommend updating the configuration to enable type-aware lint rules:

```js
export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...

      // Remove tseslint.configs.recommended and replace with this
      tseslint.configs.recommendedTypeChecked,
      // Alternatively, use this for stricter rules
      tseslint.configs.strictTypeChecked,
      // Optionally, add this for stylistic rules
      tseslint.configs.stylisticTypeChecked,

      // Other configs...
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```

You can also install [eslint-plugin-react-x](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-x) and [eslint-plugin-react-dom](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-dom) for React-specific lint rules:

```js
// eslint.config.js
import reactX from 'eslint-plugin-react-x'
import reactDom from 'eslint-plugin-react-dom'

export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...
      // Enable lint rules for React
      reactX.configs['recommended-typescript'],
      // Enable lint rules for React DOM
      reactDom.configs.recommended,
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```
