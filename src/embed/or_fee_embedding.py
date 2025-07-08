import os, psycopg2, tqdm
from openai import OpenAI                        # ← v1.x client

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

conn = psycopg2.connect(dbname="epr", user="epr",
                        host="db", password="epr")
cur  = conn.cursor(name="fee_cursor")

cur.execute("""
    SELECT material_class,
           covered_material,
           material_type,
           base_fee_low,  sim_low, disposal_low,  rate_cents_lb_low,
           base_fee_high, sim_high, disposal_high, rate_cents_lb_high,
           doc_id
    FROM   or_fee
    WHERE  embedding IS NULL
""")

batch, meta = [], []
for (
    cls, mat, typ,
    b_low, s_low, d_low, rate_low,
    b_high, s_high, d_high, rate_high,
    doc_id
) in tqdm.tqdm(cur, desc="embedding rows"):

    prompt = (
        f"{cls} | {typ} | {mat} | "
        f"base_low {b_low} | sim_low {s_low} | disp_low {d_low} | rate_low {rate_low} | "
        f"base_high {b_high} | sim_high {s_high} | disp_high {d_high} | rate_high {rate_high}"
    )
    batch.append(prompt)
    meta.append((doc_id, mat))

    if len(batch) == 90:
        # v1.x call
        embs = client.embeddings.create(
            model="text-embedding-3-small",
            input=batch
        ).data
        with conn, conn.cursor() as up:
            for e, (doc, mat_) in zip(embs, meta):
                up.execute(
                    "UPDATE or_fee SET embedding = %s "
                    "WHERE doc_id = %s AND covered_material = %s",
                    (e.embedding, doc, mat_)
                )
        batch, meta = [], []

# flush remainder
if batch:
    embs = client.embeddings.create(
        model="text-embedding-3-small",
        input=batch
    ).data
    with conn, conn.cursor() as up:
        for e, (doc, mat_) in zip(embs, meta):
            up.execute(
                "UPDATE or_fee SET embedding = %s "
                "WHERE doc_id = %s AND covered_material = %s",
                (e.embedding, doc, mat_)
            )

print("✅ all fee rows now have embeddings")
