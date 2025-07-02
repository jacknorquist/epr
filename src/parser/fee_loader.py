# src/parser/pdf_or_fee.py
import sys, uuid
import psycopg2, psycopg2.extras
from datetime import date
from pathlib import Path

STATE = sys.argv[1]
FEEFILE = Path("/code/data/raw/OR/fee.py")


# 1. Load combined_data_full list
spec = {}
exec(FEEFILE.read_text(), spec)
combined_data_full = spec["combined_data_full"]

# 2. Convert to rows (basic normalization if needed)
import pandas as pd

fee_df = pd.DataFrame(combined_data_full, columns=[
    "material_class",
    "covered_material",
    "material_type",
    "base_fee_low",
    "sim_low",
    "disposal_low",
    "rate_cents_lb_low",
    "base_fee_high",
    "sim_high",
    "disposal_high",
    "rate_cents_lb_high"
])

# Optional: print preview
print(f"✔ Loaded {len(fee_df)} rows from combined_data_full")

# 3. Connect to DB
conn = psycopg2.connect(dbname="epr", user="epr", host="db", password="epr")
psycopg2.extras.register_uuid()
cur = conn.cursor()

doc_id = uuid.uuid4()
cur.execute(
    "INSERT INTO docs (doc_id,state,type,rev_date,src_url) VALUES (%s,%s,%s,%s,%s)",
    (doc_id, STATE, "fee_manual", date.today(), FEEFILE.name)
)

# 4. Prepare table
cur.execute("""
  CREATE TABLE IF NOT EXISTS or_fee (
    material_class      TEXT,
    covered_material    TEXT,
    material_type       TEXT,
    base_fee_low        NUMERIC,
    sim_low             NUMERIC,
    disposal_low        NUMERIC,
    rate_cents_lb_low   NUMERIC,
    base_fee_high       NUMERIC,
    sim_high            NUMERIC,
    disposal_high       NUMERIC,
    rate_cents_lb_high  NUMERIC,
    eff_date            DATE,
    doc_id              UUID REFERENCES docs(doc_id)
  );
  DELETE FROM or_fee WHERE doc_id = %s;
""", (doc_id,))


# 5. Insert rows
for row in fee_df.itertuples(index=False):
    cur.execute("""
        INSERT INTO or_fee (
          material_class, covered_material, material_type,
          base_fee_low, sim_low, disposal_low, rate_cents_lb_low,
          base_fee_high, sim_high, disposal_high, rate_cents_lb_high,
          eff_date, doc_id
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        row.material_class, row.covered_material, row.material_type,
        row.base_fee_low, row.sim_low, row.disposal_low, row.rate_cents_lb_low,
        row.base_fee_high, row.sim_high, row.disposal_high, row.rate_cents_lb_high,
        date.today(), doc_id
    ))


conn.commit()
print(f"✔ Loaded {len(fee_df)} Oregon fee rows from {FEEFILE}")
