CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE docs (
  doc_id    UUID PRIMARY KEY,
  state     TEXT NOT NULL,
  type      TEXT NOT NULL,
  rev_date  DATE NOT NULL,
  src_url   TEXT NOT NULL
);

CREATE TABLE chunks (
  chunk_id UUID PRIMARY KEY,
  doc_id   UUID REFERENCES docs(doc_id),
  text     TEXT,
  emb      VECTOR(3072)
);
CREATE INDEX ON chunks USING hnsw (emb vector_l2_ops);

CREATE TABLE or_fee (
  material_class   INT,
  rate_cents_lb    NUMERIC,
  eff_date         DATE,
  doc_id           UUID REFERENCES docs(doc_id)
);
CREATE INDEX ON or_fee (material_class);