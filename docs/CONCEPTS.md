# Academic Concepts: Serving Data for Analytics & Machine Learning

## 1. What is Data Serving?
**Data Serving** is the operational phase of data engineering where processed, cleaned, aggregated, and modeled data is exposed to downstream applications, APIs, user interfaces, or external services for fast, reliable, low-latency consumption.

In traditional analytics workflows, data is processed in batches (offline ETL). However, end-user applications (such as web apps, mobile apps, or recommendation widgets) cannot wait minutes or hours for batch jobs to finish. The **Serving Layer** bridges this gap by structuring data into application-optimized schemas, enabling sub-millisecond retrieval.

---

## 2. Why Not Directly Query Raw Data?
Querying raw files directly (e.g., executing queries on unindexed raw CSVs like `u.data` or `u.item`) creates major engineering bottlenecks:
1. **High Query Latency**: A raw CSV must be repeatedly read from disk and parsed row-by-row into memory on every incoming API request.
2. **Lack of Indexing**: Raw text files do not support B-Tree or Hash indexes. Searching for a movie by ID or title requires a full table scan ($O(N)$ complexity).
3. **Expensive On-the-Fly ML Computations**: Calculating pairwise cosine similarity across $N$ movies has a computational complexity of $O(N^2)$. Running this inside an HTTP request handler would cause request timeouts, server resource exhaustion, and terrible user experience.
4. **Data Inconsistency**: Raw data often contains missing values, malformed fields, and unvalidated ranges (e.g. ratings outside 1-5). Application logic would have to re-clean data on every single request.

---

## 3. What is a Data Serving Layer?
The **Data Serving Layer** is the architectural component responsible for delivering transformed data products to consumers with high throughput and low latency.
- It sits between the **data storage engine** (DuckDB / Parquet) and the **client application** (React web application).
- In our project, the Data Serving Layer is implemented using **FastAPI**. It exposes parameterized REST endpoints, enforces strong Pydantic schemas, handles pagination, records query execution metrics, and connects to an embedded columnar analytical engine.

---

## 4. What is a "Data Product"?
In modern data engineering (and Data Mesh architectures), a **Data Product** is an autonomous, reliable package that encapsulates:
- Cleaned and enriched analytical datasets
- Applied business and machine learning logic (e.g., similarity scores, Bayesian popularity)
- An operational access contract (REST API with OpenAPI / Swagger specification)
- Service Level Objectives (SLOs) such as sub-10ms response latency

Our Movie Recommendation Service operates as a true Data Product: any consumer (web frontend, mobile app, internal analytics dashboard, or third-party service) can query `/api/movies/{id}/recommendations` to receive ranked, high-confidence recommendations without knowing anything about TF-IDF formulas or raw MovieLens file formats.

---

## 5. Offline / Batch Processing vs. Online Data Serving

| Dimension | Offline / Batch Processing | Online Data Serving |
|---|---|---|
| **Goal** | Heavy data transformation, ML training & vectorization | Low-latency response to client requests |
| **Execution Trigger** | Scheduled cron job, pipeline CLI (`run_pipeline.py`) | Interactive user action (e.g. search, click) |
| **Latency Tolerance**| Seconds to hours | Sub-10 milliseconds (< 100ms maximum) |
| **Compute Profile** | High CPU, memory-intensive, vector operations | Fast lookups, indexed joins, minimal CPU |
| **Storage Target** | Data lakes, raw folders, intermediate parquet | Columnar serving store (DuckDB), key-value cache |

---

## 6. Why Precompute Recommendations?
In a Content-Based Recommendation system:
1. Each movie is vectorized into high-dimensional TF-IDF space (e.g. 1,683 movies $\times$ 6,037 n-gram features).
2. Pairwise Cosine Similarity computes $1,683 \times 1,683 = 2,832,489$ similarity dot products.
3. For each movie, scores must be sorted to extract the Top-$K$ closest matches.

If this algorithm were executed online during an API request:
- Every user request would take **several seconds**, choking the web server.
- The server could not scale to support concurrent users.

**The Solution: Precomputation**
By computing the top 15 recommendations per movie once during the batch pipeline and storing them in an indexed table (`recommendations`), the online API simply executes:
```sql
SELECT r.rank, m.title, m.genres, r.similarity_score, s.avg_rating
FROM recommendations r
JOIN movies m ON r.recommended_movie_id = m.movie_id
JOIN ratings_summary s ON m.movie_id = s.movie_id
WHERE r.movie_id = :target_movie_id
ORDER BY r.rank ASC
LIMIT 10;
```
This indexed join executes in **1 to 5 milliseconds**, providing an instantaneous response to the user.

---

## 7. What is DuckDB and Why Use It?
**DuckDB** is an embedded analytical (OLAP) database engine—often called the "SQLite for Analytics."

### Key Advantages for Data Serving:
1. **Columnar Vectorized Execution**: Reads only the columns needed for a query, processing data in CPU vector chunks (SIMD).
2. **Zero-Server Overhead**: Runs in-process inside the Python FastAPI application without requiring a separate database server (like PostgreSQL or MySQL).
3. **High Concurrency for Reads**: Supports concurrent read-only queries with virtually zero memory overhead.
4. **Native Parquet Integration**: Can query and export Parquet files directly without intermediate data translation.
5. **Sub-Millisecond Query Times**: Perfect for serving precomputed analytics and recommendations to APIs.

---

## 8. Why Use Parquet?
**Apache Parquet** is an open-source, columnar storage format:
- **Efficient Compression**: Achieves 70–90% file size reduction compared to CSV (e.g. raw ratings CSV is ~2 MB; Parquet is ~20 KB).
- **Column Pruning**: When querying `title` and `avg_rating`, DuckDB reads only those specific byte streams from disk, ignoring all other columns.
- **Embedded Schema**: Column names, data types, and statistics (min/max per row group) are embedded in the file metadata, eliminating parsing errors.

---

## 9. Request Lifecycle: What Happens When a User Searches for a Movie?
1. **User Action**: The user types `"Star Wars"` in the frontend search bar.
2. **Debounced HTTP Request**: The React app sends an asynchronous `GET /api/movies/search?q=Star%20Wars` request.
3. **FastAPI Route**: The endpoint receives the query and validates the input parameters using Pydantic.
4. **Data Service**: The service executes a parameterized SQL query on the DuckDB serving store:
   ```sql
   SELECT m.movie_id, m.title, m.genres, s.avg_rating, s.popularity_score
   FROM movies m
   LEFT JOIN ratings_summary s ON m.movie_id = s.movie_id
   WHERE m.title ILIKE ?
   ORDER BY s.popularity_score DESC
   LIMIT 20;
   ```
5. **Execution & Latency Tracking**: DuckDB uses the title index to locate matching records in ~2 ms. The execution time is captured.
6. **Response Serialization**: The matching records are validated against `SearchResponse` Pydantic model and returned as JSON with the header `X-Process-Time-Ms`.
7. **UI Update**: The React autocomplete dropdown updates seamlessly without refreshing the page.

---

## 10. Request Lifecycle: What Happens When Recommendations are Requested?
1. **User Action**: User selects `"Star Wars (1977)"` (Movie ID: 50).
2. **HTTP Request**: The frontend calls `GET /api/movies/50/recommendations?top_k=10`.
3. **Serving Lookup**: The Recommendation Service checks the DuckDB `recommendations` table for `movie_id = 50`.
4. **Serving Query Execution**:
   - DuckDB retrieves the precomputed recommendations (e.g. Return of the Jedi, The Empire Strikes Back, Starship Troopers).
   - Joins with `ratings_summary` to attach live average ratings and vote counts.
5. **Fallback Check**: If the movie has no recommendations or low similarity, the engine seamlessly switches to the `popular_movies` table, marking `is_fallback = true` with a clear explanation.
6. **JSON Delivery**: The response returns the ranked list, cosine similarity scores, and exact query time (~3 ms).
7. **Frontend Render**: The React application renders the movie spotlight card and recommendation cards with similarity percentage badges.

---

## 11. Separation of Responsibilities in the Architecture

```
[Raw Layer]       --> MovieLens raw text files (u.item, u.data)
[Processing]      --> Python Batch Pipeline (Ingest, Clean, Transform, TF-IDF ML)
[Serving Store]   --> DuckDB Columnar Database + Parquet Files
[Serving API]     --> FastAPI REST Endpoints (Data Product)
[Client / App]    --> React UI (Modern Data Product Dashboard)
```
Each layer has a single, well-defined responsibility, ensuring modularity, maintainability, and enterprise-grade performance.
