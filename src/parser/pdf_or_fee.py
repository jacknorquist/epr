# src/parser/pdf_or_fee.py
import sys, pathlib, uuid
import camelot
import psycopg2, psycopg2.extras
from datetime import date

STATE   = sys.argv[1]           # e.g. "OR"
PDFPATH = pathlib.Path(sys.argv[2])

# 1) Extract all tables from the known pages (you may need to adjust pages="5-10")
tables = camelot.read_pdf(str(PDFPATH), pages="1-20", flavor="lattice")
# 2) Find the one with 60 rows
fee_df = next(
    tbl.df for tbl in tables
    if tbl.df.shape[0] >= 60 and "material_class" in tbl.df.columns[0].lower()
)
# 3) Clean it up
fee_df.columns = fee_df.iloc[0]           # first row as header
fee_df = fee_df.drop(0).reset_index(drop=True)
fee_df = fee_df[["Material Class","Fee (cents per lb)"]]
fee_df.columns = ["material_class","rate_cents_lb"]
fee_df = fee_df.astype({"material_class":int,"rate_cents_lb":float})

# 4) Connect & register doc
conn = psycopg2.connect(dbname="epr", user="epr", host="db", password="epr")
psycopg2.extras.register_uuid()
cur = conn.cursor()
doc_id = uuid.uuid4()
cur.execute(
    "INSERT INTO docs (doc_id,state,type,rev_date,src_url) VALUES (%s,%s,%s,%s,%s)",
    (doc_id, STATE, "fee_pdf", date.today(), PDFPATH.name)
)

# 5) Create/clear or_fee
cur.execute("""
  CREATE TABLE IF NOT EXISTS or_fee (
    material_class   INT,
    rate_cents_lb    NUMERIC,
    eff_date         DATE,
    doc_id           UUID REFERENCES docs(doc_id)
  );
  DELETE FROM or_fee WHERE doc_id = %s;
""", (doc_id,))

# 6) Insert rows
for cls, rate in fee_df.itertuples(index=False):
    cur.execute(
      "INSERT INTO or_fee (material_class, rate_cents_lb, eff_date, doc_id) VALUES (%s,%s,%s,%s)",
      (cls, rate, date.today(), doc_id)
    )

conn.commit()
print(f"✔ loaded {len(fee_df)} Oregon fee rows from PDF")
