import sys, uuid, pathlib, re
from dotenv import load_dotenv
import os
import pdfminer.high_level, markdownify
import psycopg2, psycopg2.extras
import openai
from datetime import date

load_dotenv()
client = openai.OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

STATE   = sys.argv[1]
PDFPATH = pathlib.Path(sys.argv[2])
CHUNK_LEN = 1_000
OVERLAP   = 100
# ----------------------------

def chunk_text(text, size=CHUNK_LEN, overlap=OVERLAP):
    clean = re.sub(r'\s+', ' ', text).strip()
    for i in range(0, len(clean), size - overlap):
        yield clean[i : i + size]

def main():
    # 1) extract text and convert to markdown
    raw_text = pdfminer.high_level.extract_text(PDFPATH)
    md_text  = markdownify.markdownify(raw_text)

    # 2) connect DB
    conn = psycopg2.connect(
        dbname="epr",
        user="epr",
        password="epr",
        host="db")
    psycopg2.extras.register_uuid()
    cur  = conn.cursor()

    # 3) insert into docs table
    doc_id = uuid.uuid4()
    cur.execute(
        "INSERT INTO docs (doc_id,state,type,rev_date,src_url) VALUES (%s,%s,%s,%s,%s)",
        (doc_id, STATE, "rule_pdf", date.today(), str(PDFPATH.name))
    )

    # 4) chunk, embed, insert into chunks
    for chunk in chunk_text(md_text):
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=chunk
        )
        emb = response.data[0].embedding
        cur.execute(
            "INSERT INTO chunks (chunk_id,doc_id,text,emb) VALUES (%s,%s,%s,%s)",
            (uuid.uuid4(), doc_id, chunk, emb)
        )

    conn.commit()
    print(f"✔ loaded {PDFPATH.name} into docs & chunks")
    conn.close()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python pdf_to_chunks.py OR data/raw/OR/CAAApprovedPlan.pdf")
        sys.exit(1)
    main()
