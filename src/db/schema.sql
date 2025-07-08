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

DROP TABLE IF EXISTS or_fee CASCADE;

CREATE TABLE or_fee (
  material_class        TEXT,
  covered_material      TEXT,
  material_type         TEXT,

  base_fee_low          NUMERIC,
  sim_low               NUMERIC,
  disposal_low          NUMERIC,
  rate_cents_lb_low     NUMERIC,

  base_fee_high         NUMERIC,
  sim_high              NUMERIC,
  disposal_high         NUMERIC,
  rate_cents_lb_high    NUMERIC,

  eff_date              DATE,
  doc_id                UUID REFERENCES docs(doc_id),

  embedding             VECTOR(1536)
);

CREATE INDEX IF NOT EXISTS or_fee_embedding_idx
  ON or_fee USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);

CREATE INDEX IF NOT EXISTS or_fee_material_class_idx
  ON or_fee (material_class);
