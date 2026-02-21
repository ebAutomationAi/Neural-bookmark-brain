---
name: analyze-fastapi-backend
description: Analyzes and modifies FastAPI routes, request/response models, and backend structure. Ensures consistency in schemas, preserves dependency injection patterns, and maintains modular router structure. Use when working with FastAPI endpoints, modifying routes, updating Pydantic models, or refactoring backend code.
---

# Analyze FastAPI Backend

## Quick Start

When analyzing or modifying FastAPI backend code:

1. **Review existing routers** before making changes
2. **Ensure schema consistency** across request/response models
3. **Preserve dependency injection** patterns
4. **Avoid modifying unrelated modules**

## Workflow Checklist

Before modifying any FastAPI component:

- [ ] Review existing router structure and route definitions
- [ ] Check related schemas (request/response models) for consistency
- [ ] Identify dependency injection points (Depends, get_db, get_settings, etc.)
- [ ] Verify no unrelated modules will be affected
- [ ] Ensure type hints are present and correct

## Key Principles

### 1. Router Review

Before modifying routes:
- Check if routes exist in `app/main.py` or separate router files
- Understand existing route patterns and conventions
- Identify related routes that might need updates
- Verify route tags, status codes, and response models

### 2. Schema Consistency

When working with request/response models:
- Ensure Pydantic models in `app/schemas.py` match database models
- Verify field types and optional/required fields are consistent
- Check that response models include all necessary fields
- Maintain naming conventions (e.g., `BookmarkCreate`, `BookmarkResponse`)

### 3. Dependency Injection

Preserve existing patterns:
- Use `Depends(get_db)` for database sessions
- Use `Depends(get_settings)` for configuration
- Use service dependencies like `get_embedding_service()`
- Maintain async/await patterns with `AsyncSession`
- Don't bypass dependency injection by importing directly

### 4. Scope Isolation

Avoid changing unrelated modules:
- Only modify files directly related to the change
- Don't refactor unrelated routes or services
- Keep business logic separated from route definitions
- Preserve existing environment configuration patterns

## Common Patterns

### Route Definition Pattern

```python
@app.get("/endpoint", response_model=ResponseModel, tags=["Tag"])
async def route_handler(
    db: AsyncSession = Depends(get_db),
    settings = Depends(get_settings)
):
    # Route logic here
    pass
```

### Schema Update Pattern

When updating schemas:
1. Check existing base models (`BookmarkBase`, etc.)
2. Update request model if needed (`BookmarkCreate`, etc.)
3. Update response model if needed (`BookmarkResponse`, etc.)
4. Verify all fields match database model structure

### Dependency Pattern

```python
# Database dependency
async def route(db: AsyncSession = Depends(get_db)):
    pass

# Settings dependency  
async def route(settings = Depends(get_settings)):
    pass

# Service dependency
async def route(service = Depends(get_embedding_service)):
    pass
```

## Anti-Patterns to Avoid

❌ **Don't** bypass dependency injection:
```python
# Bad
from app.database import AsyncSessionLocal
session = AsyncSessionLocal()

# Good
async def route(db: AsyncSession = Depends(get_db)):
    pass
```

❌ **Don't** modify unrelated routes when adding new functionality

❌ **Don't** create inconsistent schema field names or types

❌ **Don't** merge routers unnecessarily (keep them modular)

## Verification Steps

After making changes:

1. Verify all imports are correct
2. Check that response models match route return types
3. Ensure dependency injection is used consistently
4. Confirm no unrelated modules were modified
5. Validate that type hints are present
