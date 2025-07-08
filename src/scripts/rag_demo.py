# scripts/rag_fee_demo.py
import sys, os, psycopg2, textwrap
from openai import OpenAI

QUESTION = sys.argv[1] if len(sys.argv) > 1 else "fee for rigid plastic bottles"
TOP_K    = 3

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 1️⃣ embed the question
q_emb = client.embeddings.create(
    model="text-embedding-3-small",
    input=[QUESTION]
).data[0].embedding

# 2️⃣ similarity search in Postgres
conn = psycopg2.connect(dbname="epr", user="epr", host="db", password="epr")
cur  = conn.cursor()
cur.execute("""
    SELECT
      material_class,
      covered_material,
      material_type,
      rate_cents_lb_low,
      rate_cents_lb_high
    FROM or_fee
    ORDER BY embedding <=> %s::vector
    LIMIT %s;
""", (q_emb, TOP_K))

rows = cur.fetchall()

# build context bullets
context = "\n".join(
    f"- {cls} :: {typ} :: {mat} → {low}–{high} ¢/lb"
    for cls, mat, typ, low, high in rows
)

# 3️⃣ ask the LLM
system = "You are an EPR fee assistant. Base answers only on the provided context."
user   = f"Question: {QUESTION}\n\nContext:\n{context}\n\nAnswer in one short paragraph."

resp = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role":"system","content":system},
              {"role":"user","content":user}],
    temperature=0.2
)

print("\n=== LLM answer ===\n")
print(textwrap.fill(resp.choices[0].message.content, 100))
print("\n=== Rows used ===\n")
print(context)
