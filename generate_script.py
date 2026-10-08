import os, json
from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
MODEL = "gemini-flash-latest"
CFG = types.GenerateContentConfig(response_mime_type="application/json")

def ask(prompt):
    r = client.models.generate_content(model=MODEL, contents=prompt, config=CFG)
    return json.loads(r.text)

WRITE_RULES = (
    "Kamu penulis naskah video edukasi pendek (35-45 detik, sekitar 90-110 kata) "
    "dalam bahasa Indonesia gaya ngobrol. ATURAN: "
    "1) Hook 3 detik pertama harus fakta spesifik, angka, atau pertanyaan yang bikin penasaran. "
    "DILARANG buka dengan kalimat umum seperti 'Tahukah kamu' atau 'Pernahkah kamu'. "
    "2) Satu topik sempit dan spesifik, bukan topik luas. "
    "3) Kalimat pendek, gaya omongan, ada satu detail mengejutkan tiap 5-8 detik. "
    "4) Hanya fakta yang kamu yakin benar, jangan mengarang angka. "
    "5) Tutup dengan satu kalimat penutup yang nendang. "
    "Balas JSON: {\"topic\": str, \"hook\": str, \"scenes\": "
    "[{\"narration\": str, \"visual_keyword\": str (bahasa Inggris, 2-3 kata)}]} "
    "dengan 6-8 scene."
)

def write(feedback=None, previous=None):
    p = WRITE_RULES
    if previous:
        p += "\n\nNASKAH SEBELUMNYA:\n" + json.dumps(previous, ensure_ascii=False)
        p += "\n\nCATATAN JURI, PERBAIKI:\n" + feedback
    else:
        p += "\n\nPilih sendiri satu topik edukasi umum yang menarik dan spesifik."
    return ask(p)

def judge(script):
    p = (
        "Kamu juri keras untuk naskah video edukasi pendek. Nilai 1-10: "
        "hook (spesifik dan bikin penasaran), spesifik (bukan generik), "
        "lisan (enak diucapkan), akurasi (fakta benar, curiga pada angka aneh). "
        "Balas JSON: {\"hook\": int, \"spesifik\": int, \"lisan\": int, "
        "\"akurasi\": int, \"catatan\": str (saran perbaikan konkret)}.\n\n"
        "NASKAH:\n" + json.dumps(script, ensure_ascii=False)
    )
    return ask(p)

best, best_score = None, -1
script, notes = None, None
for i in range(3):
    script = write(notes, script) if i else write()
    j = judge(script)
    score = min(j["hook"], j["spesifik"], j["lisan"], j["akurasi"])
    print("Putaran", i + 1, "skor terendah:", score, "|", j["catatan"])
    if score > best_score:
        best, best_score = script, score
    if score >= 8:
        break
    notes = j["catatan"]

with open("script.json", "w", encoding="utf-8") as f:
    json.dump(best, f, ensure_ascii=False, indent=2)
print("\nNASKAH FINAL (skor %d):" % best_score)
print(json.dumps(best, ensure_ascii=False, indent=2))
