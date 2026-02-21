---
name: embedding-pipeline-review
description: Reviews embedding generation, semantic search, and vector storage logic. Identifies where embeddings are generated, verifies consistent model usage, prevents duplicate computation, and ensures retrieval logic matches storage format. Use when reviewing embedding pipelines, semantic search implementations, vector database operations, or when the user mentions embeddings, vector search, or semantic similarity.
---

# Embedding Pipeline Review

## Quick Start

When reviewing embedding-related code:

1. **Identify embedding generation points** - Find all places where embeddings are created
2. **Verify model consistency** - Ensure the same model and configuration is used throughout
3. **Check for duplicate computation** - Avoid regenerating embeddings unnecessarily
4. **Validate storage-retrieval match** - Ensure query embeddings match stored embedding format

## Review Checklist

### 1. Embedding Generation Points

- [ ] Locate all `generate_embedding()` or similar calls
- [ ] Identify where embeddings are created (services, routes, background jobs)
- [ ] Check if embeddings are generated synchronously or asynchronously
- [ ] Verify embedding generation happens at the right stage (on creation, on update, or on-demand)

### 2. Model Consistency

- [ ] Verify the same embedding model is used for generation and queries
- [ ] Check that model configuration (dimensions, normalization) is consistent
- [ ] Ensure model version/name matches across all usage points
- [ ] Validate that preprocessing (text truncation, cleaning) is consistent

**Common issues:**
- Different models used for storage vs. retrieval
- Inconsistent normalization (some normalized, some not)
- Mismatched dimensions between model output and database schema

### 3. Duplicate Computation Prevention

- [ ] Check if embeddings are cached or stored after generation
- [ ] Verify embeddings aren't regenerated unnecessarily (e.g., on every read)
- [ ] Look for opportunities to batch embedding generation
- [ ] Ensure embeddings persist in database/storage when appropriate

**Red flags:**
- Embeddings generated in request handlers without caching
- Same text embedded multiple times in the same flow
- Missing checks for existing embeddings before generation

### 4. Storage-Retrieval Format Match

- [ ] Verify embedding dimensions match database schema
- [ ] Check that query embeddings use the same format as stored embeddings
- [ ] Ensure similarity metrics (cosine, euclidean) match storage index type
- [ ] Validate vector type compatibility (pgvector, numpy array, list, etc.)

**Key checks:**
- Database column type matches embedding dimension (e.g., `vector(384)`)
- Query uses same normalization as stored embeddings
- Index type (IVFFlat, HNSW) matches similarity function
- Conversion between formats (list ↔ numpy ↔ database) is correct

## Common Patterns

### Pattern 1: Service-Based Generation

```python
# Good: Centralized embedding service
embedding_service = get_embedding_service()
embedding = embedding_service.generate_embedding(text)

# Bad: Direct model instantiation in multiple places
model = SentenceTransformer("model-name")
embedding = model.encode(text)
```

### Pattern 2: Batch Processing

```python
# Good: Batch generation for multiple texts
embeddings = embedding_service.generate_batch_embeddings(texts)

# Bad: Loop with individual generation
embeddings = [embedding_service.generate_embedding(text) for text in texts]
```

### Pattern 3: Storage Format

```python
# Good: Consistent format conversion
embedding_list = embedding.tolist()  # numpy → list
normalized = normalize(embedding_list)  # Normalize before storage
db_record.embedding = normalized  # Store as list/vector

# Bad: Inconsistent formats
db_record.embedding = embedding  # numpy array (may not work)
query_embedding = list(embedding)  # Different conversion method
```

### Pattern 4: Query Matching

```python
# Good: Query uses same preprocessing and normalization
query_embedding = embedding_service.generate_query_embedding(query)
results = db.query_by_similarity(query_embedding, metric='cosine')

# Bad: Different preprocessing for queries
query_embedding = model.encode(query.lower())  # Different preprocessing
results = db.query_by_similarity(query_embedding, metric='euclidean')  # Wrong metric
```

## Anti-Patterns to Avoid

❌ **Don't** use different models for storage and retrieval:
```python
# Bad
storage_model = SentenceTransformer("model-a")
query_model = SentenceTransformer("model-b")
```

❌ **Don't** regenerate embeddings unnecessarily:
```python
# Bad
def get_bookmark(id):
    bookmark = db.get(id)
    bookmark.embedding = generate_embedding(bookmark.text)  # Regenerates every time
    return bookmark
```

❌ **Don't** mix normalized and unnormalized embeddings:
```python
# Bad
stored_embedding = normalize(generate_embedding(text))
query_embedding = generate_embedding(query)  # Not normalized
```

❌ **Don't** ignore dimension mismatches:
```python
# Bad
model_dimension = 384
db_column = Vector(512)  # Mismatch!
```

## Verification Steps

After reviewing embedding code:

1. **Trace the flow**: Follow a text from input → embedding → storage → retrieval
2. **Check consistency**: Verify same model/config used at each step
3. **Test dimensions**: Ensure all embeddings have expected dimensions
4. **Validate format**: Confirm storage and retrieval use compatible formats
5. **Check caching**: Verify embeddings aren't regenerated unnecessarily

## Specific Checks for Common Libraries

### SentenceTransformers
- Model name consistency: `settings.EMBEDDING_MODEL`
- Dimension consistency: `settings.EMBEDDING_DIMENSION`
- Normalization: Check if `normalize_embeddings=True` is used consistently

### pgvector (PostgreSQL)
- Column type: `Vector(dimension)` matches model output
- Index type: `ivfflat` for cosine similarity, `hnsw` for euclidean
- Query operator: `<=>` for cosine distance, `<->` for euclidean distance

### Vector Databases (Pinecone, Weaviate, etc.)
- Namespace/collection configuration matches model
- Dimension configuration matches model output
- Similarity metric (cosine, dot-product, euclidean) matches normalization
