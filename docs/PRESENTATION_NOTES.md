# College Presentation Notes & Viva Preparation Guide

**Project Title:** Movie Recommendation System Using Data Serving  
**Academic Topic:** Serving Data for Analytics & ML  

---

## A. 30-Second Elevator Pitch
> *"Our project demonstrates an end-to-end Data Engineering pipeline and Data Serving architecture. Instead of computing machine learning recommendations on-the-fly or forcing client apps to parse raw CSVs, we use an offline batch pipeline to clean MovieLens data, compute content-based TF-IDF similarities, and store the results in an embedded columnar DuckDB database. A high-performance FastAPI serving layer exposes these precomputed data products with sub-5 millisecond response times to a modern React frontend."*

---

## B. 1-Minute Project Explanation
> *"In real-world data engineering, machine learning models and analytical transformations are computationally expensive and cannot be executed directly within user-facing API request cycles. Our system addresses this by enforcing a strict separation between Data Processing and Data Serving.*  
> 
> *In the offline pipeline, we ingest 100,000 MovieLens ratings and 1,682 movies, apply Bayesian shrinkage to prevent low-sample rating bias, and calculate pairwise TF-IDF cosine similarities. We then materialize the Top-15 recommendations per movie into serving-ready DuckDB tables and Parquet files.*  
> 
> *Our FastAPI serving layer acts as a true Data Product: when a user searches for a movie like 'Star Wars' or 'Toy Story', the API performs an indexed lookup against DuckDB in under 3 milliseconds, providing instant recommendations without running ML inference. A responsive React web application displays recommendations, metrics, and real-time analytical distributions."*

---

## C. Architecture Walkthrough
1. **Raw Storage Layer**: Raw MovieLens 100K files (`u.item`, `u.data`, `u.genre`).
2. **Batch Processing Pipeline (`pipeline/`)**:
   - `ingest.py`: Validates schemas, row counts, duplicate IDs, and rating bounds.
   - `clean.py`: Normalizes titles, extracts 4-digit release years, and consolidates 19 binary genre flags into standardized strings.
   - `transform.py`: Calculates average ratings and Bayesian popularity scores ($W$).
   - `recommend.py`: Fits TF-IDF on enriched metadata and precomputes Top-15 cosine similarity matches.
3. **Serving Storage Layer (`data/serving/`)**:
   - DuckDB database (`movies.duckdb`) with indexed tables (`movies`, `ratings_summary`, `recommendations`, `popular_movies`).
   - Parquet backups for zero-copy columnar analytics.
4. **Data Serving API (`backend/`)**:
   - FastAPI REST endpoints providing paginated movie exploration, relevance search, recommendations, and analytics.
5. **Data Product Presentation (`frontend/`)**:
   - React + Vite dashboard consuming serving endpoints with real-time latency indicators and analytical visualizations.

---

## D. Data Pipeline Explanation
- **Step 1 (Ingestion)**: Reads raw tab/pipe delimited files with Latin-1 encoding, verifying referential integrity (ensuring every rating maps to a valid movie).
- **Step 2 (Cleaning)**: Deduplicates records, extracts release years via regular expressions, and cleans strings.
- **Step 3 (Transformation)**: Calculates movie rating counts ($v$), mean rating ($R$), and global mean ($C$). Applies Bayesian formula:
  $$W = \left(\frac{v}{v + m}\right) \cdot R + \left(\frac{m}{v + m}\right) \cdot C$$
  where $m = 15$ minimum votes threshold. This prevents a movie with a single 5-star review from appearing more popular than a movie with hundreds of 4.5-star reviews.
- **Step 4 (Recommendation Engine)**: Builds an $N$-gram TF-IDF matrix over combined titles and genres, computes cosine similarity, and extracts Top-15 recommendations per movie.
- **Step 5 (Serving Store Build)**: Loads dataframes directly into DuckDB serving tables, creates B-Tree indexes, and exports Parquet files.

---

## E. Recommendation Algorithm Explanation
- **Algorithm**: Content-Based Filtering using TF-IDF (Term Frequency-Inverse Document Frequency) and Cosine Similarity.
- **Feature Representation**: Enriched text combining normalized title, doubled genre tokens (for term frequency weighting), and release era.
- **Mathematical Formula**:
  $$\text{Cosine Similarity}(A, B) = \frac{A \cdot B}{\|A\| \|B\|}$$
- **Self-Match Exclusion**: A movie's similarity to itself is set to $-1.0$ so it is never recommended to itself.
- **Fallback Logic**: If a movie has sparse metadata or zero similar items, the system gracefully serves the Top Bayesian popular movies, flagging `is_fallback = true` with a clear explanation.

---

## F. Data Serving Explanation
- The serving layer transforms internal analytical representations into stable, consumption-ready data products.
- Instead of exposing raw database tables or running queries across millions of raw rows, the API queries pre-aggregated tables where `movie_id` is indexed.
- The serving layer enforces contracts via Pydantic models, adds timing headers (`X-Process-Time-Ms`), and handles pagination and error status codes.

---

## G. Why DuckDB?
1. **Embedded OLAP**: Runs directly inside the Python process with zero operational maintenance or server setup.
2. **Columnar Vectorized Engine**: Reads only required columns and processes thousands of rows per CPU cycle.
3. **Low Latency**: Delivers sub-5 millisecond query execution times for analytical lookups and joins.
4. **Direct Parquet Support**: Queries and exports Parquet files natively.

---

## H. Why FastAPI?
1. **Asynchronous Performance**: Built on Starlette and Pydantic, making it one of the fastest Python web frameworks.
2. **Automatic OpenAPI/Swagger Documentation**: Generates interactive API documentation at `/docs` out-of-the-box.
3. **Type Safety & Data Validation**: Rejects malformed requests automatically before they reach the database layer.

---

## I. Why Precompute Recommendations?
- Calculating cosine similarity across all movies is an $O(N^2)$ operation.
- In MovieLens 100K, pairwise comparison requires evaluating over 2.8 million combinations.
- Doing this live during an HTTP request causes severe latency spikes and crashes under concurrent traffic.
- Precomputing recommendations in batch and saving them in an indexed serving table turns an $O(N^2)$ computation into an $O(1)$ indexed lookup!

---

## J. Top 15 Viva Questions and Answers

### Q1: What is Data Serving?
**Answer:** Data Serving is the layer in a data architecture that delivers processed, cleaned, and aggregated data to user-facing applications, APIs, or dashboards with high availability and low latency.

### Q2: Why is Data Serving required in addition to Data Processing?
**Answer:** Data Processing focuses on heavy computations (ETL, machine learning, transformations), which are slow and resource-intensive. Data Serving focuses on client consumption, organizing data into indexed tables so end-users get responses in milliseconds.

### Q3: What is the difference between Batch Processing and Online Serving?
**Answer:** Batch Processing runs periodically on large volumes of data (high latency tolerance, high throughput). Online Serving runs continuously in real-time in response to user requests (low latency tolerance, sub-second responses).

### Q4: Why are recommendations precomputed in this project?
**Answer:** Pairwise cosine similarity has quadratic $O(N^2)$ complexity. Running it on every API call would take seconds per request. Precomputing recommendations during the offline pipeline allows the API to serve them via an indexed SQL lookup in 2–4 milliseconds.

### Q5: What is a Data Product?
**Answer:** A Data Product is a packaged data asset designed for consumption. It includes the underlying data, the algorithms, and a standard access mechanism (like a documented REST API) with defined quality and latency guarantees.

### Q6: What is TF-IDF?
**Answer:** Term Frequency-Inverse Document Frequency is a numerical statistic reflecting how important a word is to a document within a collection. TF measures frequency in the document; IDF penalizes words that appear everywhere (e.g. common words) to emphasize distinctive terms.

### Q7: What is Cosine Similarity and how does it work?
**Answer:** Cosine similarity measures the cosine of the angle between two multi-dimensional vectors. It evaluates directional similarity regardless of vector magnitude, producing a score between 0.0 (completely dissimilar) and 1.0 (identical).

### Q8: What is the Bayesian Popularity formula and why did you use it?
**Answer:** A simple arithmetic average can be misleading (e.g., a movie with one 5-star rating appears better than a movie with five hundred 4.8-star ratings). The Bayesian formula:
$$W = \frac{v}{v+m} \cdot R + \frac{m}{v+m} \cdot C$$
shrinks small-sample ratings toward the global dataset mean ($C$) unless the movie has accumulated enough votes ($v \ge m$).

### Q9: Why use DuckDB instead of SQLite?
**Answer:** SQLite is a row-oriented transactional (OLTP) database optimized for single-record writes. DuckDB is a columnar analytical (OLAP) database optimized for analytical joins, aggregations, and vectorized queries, making it significantly faster for serving analytical data.

### Q10: Why use Parquet instead of CSV files?
**Answer:** Parquet is a compressed, columnar binary format. It supports column pruning (reading only needed columns), dictionary encoding, and embedded schema metadata, resulting in smaller disk space and faster read performance than plain text CSVs.

### Q11: What happens if a user searches for an unknown or unrated movie?
**Answer:** The recommendation service contains an intelligent fallback mechanism. If content similarity metadata is insufficient or absent, it falls back to the top Bayesian popular movies, setting `is_fallback = true` with a clear explanation in the response.

### Q12: How does the FastAPI serving layer connect to DuckDB?
**Answer:** We maintain a thread-safe `DuckDBClient` that opens read-only connections (`read_only=True`). This allows concurrent readers to query the database simultaneously without locking issues.

### Q13: What is the purpose of indexes in the serving database?
**Answer:** We created indexes on `movies(lower(title))`, `recommendations(movie_id)`, and `popular_movies(rank)`. Indexes allow DuckDB to find records via logarithmic B-Tree lookups ($O(\log N)$) rather than full table scans ($O(N)$).

### Q14: How can this architecture scale to millions of users and movies?
**Answer:**
1. The batch pipeline can run on distributed frameworks (like Apache Spark or Ray).
2. Serving tables can be stored in distributed analytical databases (ClickHouse / Snowflake) or cached in Redis.
3. The FastAPI layer is stateless and can be horizontally scaled behind an API gateway / load balancer.

### Q15: What are the main limitations of this content-based recommender?
**Answer:**
1. **Cold Start for New Items**: Movies with missing metadata cannot produce good content matches.
2. **Limited Serendipity**: Recommends movies strictly similar to what the user already selected, without discovering unexpected cross-genre interests (which collaborative filtering provides).
