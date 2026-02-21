---
name: frontend-architecture-review
description: Analyzes, refactors, and implements frontend components and UI logic following React + TypeScript patterns. Ensures separation of business logic from presentation, maintains modular component structure, and preserves consistent state management patterns. Use when analyzing frontend code, refactoring components, implementing new UI features, reviewing component architecture, or when the user mentions React components, UI logic, or frontend structure.
---

# Frontend Architecture Review

## Quick Start

When analyzing, refactoring, or implementing frontend components:

1. **Respect the existing architecture** (Atomic Design + Feature-based hybrid)
2. **Separate business logic from presentation** (hooks vs components)
3. **Keep components modular and reusable**
4. **Maintain consistent state management** (custom hooks pattern)
5. **Avoid unnecessary dependencies**

## Architecture Overview

The project uses a **hybrid Atomic Design + Feature-based** structure:

```
src/
├── components/
│   ├── ui/              # Atomic: Button, Input, Badge, Toast
│   ├── layout/          # Organisms: Header, Sidebar, Layout
│   ├── bookmarks/       # Feature: BookmarkCard, BookmarkGrid
│   ├── stats/           # Feature: StatCard, ProcessingProgress
│   └── search/          # Feature: SearchBar, SearchResults
├── pages/               # Dashboard, Search, Bookmarks, Statistics
├── hooks/               # Custom hooks: useBookmarks, useToast
├── services/            # API client: api.ts
└── types/               # TypeScript type definitions
```

## Workflow Checklist

Before modifying or creating frontend components:

- [ ] Identify the appropriate component category (ui/layout/feature)
- [ ] Check if similar components exist that can be reused or extended
- [ ] Determine if business logic should be in a hook or component
- [ ] Verify state management follows custom hooks pattern (no Redux/Zustand)
- [ ] Ensure API calls are centralized in `services/api.ts`
- [ ] Check that TypeScript types are defined in `types/`
- [ ] Verify component is modular and reusable

## Key Principles

### 1. Respect Existing Structure

**Component Organization:**
- **`components/ui/`**: Atomic, reusable UI primitives (Button, Input, Badge, Toast)
- **`components/layout/`**: Layout organisms (Header, Sidebar, Layout wrapper)
- **`components/[feature]/`**: Feature-specific components (BookmarkCard, SearchBar)
- **`pages/`**: Page-level components that orchestrate features

**Guidelines:**
- Don't mix atomic and feature components
- Keep layout components separate from business logic
- Place new components in the appropriate category

### 2. Separate Business Logic from Presentation

**Business Logic → Custom Hooks:**
- API calls and data fetching → `hooks/useBookmarks.ts`, `hooks/useToast.ts`
- State management → Custom hooks, not component state
- Data transformations → Hooks or utility functions

**Presentation → Components:**
- UI rendering → Components receive props and callbacks
- User interactions → Components call hook functions via props
- Visual state (expanded, hover) → Component-level `useState` is acceptable

**Example Pattern:**
```typescript
// ✅ Good: Business logic in hook
const { bookmarks, loading, search } = useBookmarks();
<SearchBar onSearch={search} />

// ❌ Bad: Business logic in component
const SearchBar = () => {
  const [bookmarks, setBookmarks] = useState([]);
  const handleSearch = async (query: string) => {
    const data = await fetch(`/api/search?q=${query}`);
    setBookmarks(await data.json());
  };
  // ...
};
```

### 3. Keep Components Modular and Reusable

**Component Design:**
- Accept props for customization (variants, sizes, callbacks)
- Use composition over configuration
- Avoid hardcoded values that limit reusability
- Export clear TypeScript interfaces for props

**Example:**
```typescript
// ✅ Good: Reusable with props
interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  onClick?: () => void;
  children: React.ReactNode;
}

// ❌ Bad: Hardcoded, not reusable
const Button = () => <button className="bg-blue-500">Click me</button>;
```

### 4. Consistent State Management

**State Management Pattern:**
- Use **custom hooks** for business logic state (`useBookmarks`, `useToast`)
- Use **component state** (`useState`) only for UI-specific state (expanded, hover, form inputs)
- **No global state management libraries** (Redux, Zustand) - use custom hooks instead
- API calls centralized in `services/api.ts`

**State Flow:**
```
Page Component
  ↓ uses hook
Custom Hook (useBookmarks)
  ↓ calls
API Service (api.ts)
  ↓ returns data
Hook updates state
  ↓ passes to
Components via props
```

**Example:**
```typescript
// ✅ Good: State in custom hook
const Dashboard = () => {
  const { bookmarks, loading, search } = useBookmarks();
  return <BookmarkGrid bookmarks={bookmarks} isLoading={loading} />;
};

// ❌ Bad: State in component, direct API calls
const Dashboard = () => {
  const [bookmarks, setBookmarks] = useState([]);
  useEffect(() => {
    fetch('/api/bookmarks').then(r => r.json()).then(setBookmarks);
  }, []);
  // ...
};
```

### 5. Avoid Unnecessary Dependencies

**Dependency Guidelines:**
- Check `package.json` before adding new dependencies
- Prefer built-in React hooks over external state libraries
- Use existing UI components from `components/ui/` before creating new ones
- Only add dependencies that solve specific problems not solvable with existing tools

**Current Stack:**
- React 18 + TypeScript 5.x
- Vite 5.x (build tool)
- Tailwind CSS 3.x (styling)
- React Router DOM (routing)
- No state management library (custom hooks only)

## Common Patterns

### Component Creation Pattern

1. **Determine component category** (ui/layout/feature)
2. **Check for existing similar components** that can be reused
3. **Define TypeScript interface** for props
4. **Extract business logic** to a hook if needed
5. **Use Tailwind CSS** for styling (utility-first)
6. **Export component** with proper types

### Hook Creation Pattern

When creating custom hooks:

```typescript
// hooks/useFeature.ts
import { useState, useEffect } from 'react';
import { api } from '../services/api';

export const useFeature = (initialFilters = {}) => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const result = await api.getData(initialFilters);
      setData(result);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  return { data, loading, error, refetch: loadData };
};
```

### Page Component Pattern

```typescript
// pages/FeaturePage.tsx
import { useFeature } from '../hooks/useFeature';
import FeatureComponent from '../components/feature/FeatureComponent';

const FeaturePage: React.FC = () => {
  const { data, loading, refetch } = useFeature();

  return (
    <div className="space-y-6">
      <FeatureComponent 
        data={data} 
        isLoading={loading}
        onRefresh={refetch}
      />
    </div>
  );
};
```

## Anti-Patterns to Avoid

❌ **Don't mix business logic with presentation:**
```typescript
// Bad: API call in component
const BookmarkCard = ({ bookmark }) => {
  const handleDelete = async () => {
    await fetch(`/api/bookmarks/${bookmark.id}`, { method: 'DELETE' });
  };
  // ...
};
```

❌ **Don't create components in wrong categories:**
```typescript
// Bad: Feature component in ui/
// components/ui/BookmarkCard.tsx ❌

// Good: Feature component in feature folder
// components/bookmarks/BookmarkCard.tsx ✅
```

❌ **Don't use global state management libraries:**
```typescript
// Bad: Adding Redux/Zustand
import { createStore } from 'redux';

// Good: Custom hooks
const useBookmarks = () => { /* ... */ };
```

❌ **Don't duplicate API logic:**
```typescript
// Bad: Direct fetch in component
const data = await fetch('/api/bookmarks');

// Good: Use centralized API service
const data = await api.getBookmarks();
```

❌ **Don't create unnecessary wrapper components:**
```typescript
// Bad: Wrapper that adds no value
const Wrapper = ({ children }) => <div>{children}</div>;

// Good: Use composition or extend existing components
```

## Verification Steps

After creating or modifying components:

1. ✅ Component is in the correct category folder
2. ✅ Business logic is separated into hooks (if needed)
3. ✅ Component accepts props for customization
4. ✅ TypeScript types are defined and exported
5. ✅ No direct API calls in components (use `services/api.ts`)
6. ✅ State management follows custom hooks pattern
7. ✅ Component is reusable and modular
8. ✅ No unnecessary dependencies added
9. ✅ Styling uses Tailwind CSS utility classes
10. ✅ Component follows existing naming conventions

## TypeScript Best Practices

- Define interfaces for all component props
- Use type imports: `import type { Bookmark } from '../types'`
- Avoid `any` types - use proper types or `unknown`
- Export types alongside components when reusable

```typescript
// ✅ Good: Proper types
interface BookmarkCardProps {
  bookmark: Bookmark;
  onEdit?: (bookmark: Bookmark) => void;
  onDelete?: (id: number) => void;
}

// ❌ Bad: Any types
interface BookmarkCardProps {
  bookmark: any;
  onEdit?: (bookmark: any) => void;
}
```
