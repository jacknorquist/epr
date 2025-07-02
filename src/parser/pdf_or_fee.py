# DOES NOT WORK #
import sys, pathlib, uuid
import camelot
import psycopg2, psycopg2.extras
from datetime import date



STATE   = sys.argv[1]
PDFPATH = pathlib.Path(sys.argv[2])

# 1. Extract from known fee pages (page 199 onward)
tables = camelot.read_pdf(str(PDFPATH), pages="199-210", flavor="lattice", strip_text="\n")

for i, tbl in enumerate(tables):
    print(f"▶ Table #{i} (page {tbl.page}, shape={tbl.df.shape})")
    print(tbl.df.head(2).to_string(index=False))

# 2. Identify correct table (first with 60+ rows and 9+ columns)
fee_df = next(
    tbl.df for tbl in tables
    if tbl.df.shape[1] >= 9 and any("Covered Material" in cell for cell in tbl.df.iloc[0])
)

# 3. Set column names based on observed layout
fee_df.columns = [
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
]

# 4. Drop header row and normalize values
fee_df = fee_df.drop(0).reset_index(drop=True)
fee_df["material_class"] = fee_df["material_class"].str.extract(r'(\d+)').astype(int)
fee_df["rate_cents_lb_low"] = fee_df["rate_cents_lb_low"].str.replace("¢/lb", "").astype(float)
fee_df["rate_cents_lb_high"] = fee_df["rate_cents_lb_high"].str.replace("¢/lb", "").astype(float)
fee_df["covered_material"] = fee_df["covered_material"].str.strip()
fee_df["material_type"] = fee_df["material_type"].str.strip()

# 5. Connect to DB
conn = psycopg2.connect(dbname="epr", user="epr", host="db", password="epr")
psycopg2.extras.register_uuid()
cur = conn.cursor()

doc_id = uuid.uuid4()
cur.execute(
    "INSERT INTO docs (doc_id,state,type,rev_date,src_url) VALUES (%s,%s,%s,%s,%s)",
    (doc_id, STATE, "fee_pdf", date.today(), PDFPATH.name)
)

# 6. Prepare `or_fee` table
cur.execute("""
  CREATE TABLE IF NOT EXISTS or_fee (
    material_class     INT,
    covered_material   TEXT,
    material_type      TEXT,
    rate_cents_lb_low  NUMERIC,
    rate_cents_lb_high NUMERIC,
    eff_date           DATE,
    doc_id             UUID REFERENCES docs(doc_id)
  );
  DELETE FROM or_fee WHERE doc_id = %s;
""", (doc_id,))

# 7. Insert rows
for row in fee_df.itertuples(index=False):
    cur.execute("""
        INSERT INTO or_fee (
          material_class, covered_material, material_type,
          rate_cents_lb_low, rate_cents_lb_high, eff_date, doc_id
        ) VALUES (%s,%s,%s,%s,%s,%s,%s)
    """, (
        row.material_class, row.covered_material, row.material_type,
        row.rate_cents_lb_low, row.rate_cents_lb_high,
        date.today(), doc_id
    ))

conn.commit()
print(f"✔ Loaded {len(fee_df)} Oregon fee rows from PDF")
