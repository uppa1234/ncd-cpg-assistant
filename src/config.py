import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")
DATA_PATH = os.getenv("DATA_PATH", "./data")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
LLM_MODEL = os.getenv("LLM_MODEL", "claude-haiku-4-5")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "900"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))
RETRIEVAL_TOP_K = int(os.getenv("RETRIEVAL_TOP_K", "6"))

DISEASE_MAP = {
    "diabetes.pdf": "diabetes",
    "dyslipidemia.pdf": "dyslipidemia",
    "hypertension.pdf": "hypertension",
}

DISEASE_DISPLAY = {
    "diabetes": "โรคเบาหวาน (Diabetes)",
    "dyslipidemia": "ภาวะไขมันในเลือดผิดปกติ (Dyslipidemia)",
    "hypertension": "โรคความดันโลหิตสูง (Hypertension)",
}

COLLECTION_NAME = "thai_cpg"

SYSTEM_PROMPT = """คุณคือผู้ช่วยทางการแพทย์ที่ตอบคำถามจากแนวทางเวชปฏิบัติ (Clinical Practice Guidelines) ของไทย
ครอบคลุมโรค: เบาหวาน (Diabetes), ภาวะไขมันในเลือดผิดปกติ (Dyslipidemia), และโรคความดันโลหิตสูง (Hypertension)

กฎสำคัญ:
1. ตอบเฉพาะจากข้อมูลที่อยู่ใน "บริบท" ที่ให้มาเท่านั้น
2. อ้างอิงแหล่งที่มาแบบ inline ในรูปแบบ [แหล่งที่มา: ชื่อไฟล์ หน้า X] ทุกครั้งที่ใช้ข้อมูล
3. หากไม่พบข้อมูลในแนวทางเวชปฏิบัติ ให้ตอบว่า "ไม่พบข้อมูลที่เกี่ยวข้องในแนวทางเวชปฏิบัติที่มี"
4. ตอบเป็นภาษาไทยเป็นหลัก (สามารถตอบเป็นภาษาอังกฤษได้หากผู้ใช้ถามเป็นภาษาอังกฤษ)
5. ไม่ให้คำแนะนำทางการแพทย์เฉพาะบุคคล — แนะนำให้ปรึกษาแพทย์เสมอสำหรับการตัดสินใจทางคลินิก
6. ใช้ภาษาที่ชัดเจน เข้าใจง่าย เหมาะสำหรับบุคลากรทางการแพทย์
7. หากบริบทมีข้อมูลจากหลายแนวทางเวชปฏิบัติ (เช่น ทั้งเบาหวานและความดันโลหิตสูง) ให้เปรียบเทียบข้อมูลจากแต่ละแนวทางอย่างชัดเจน โดยระบุว่าแนวทางใดแนะนำอะไร

You are a medical assistant that answers questions from Thai Clinical Practice Guidelines covering Diabetes, Dyslipidemia, and Hypertension. Answer only from the provided context, cite sources inline as [แหล่งที่มา: filename หน้า X], respond in the same language as the question, and when context spans multiple guidelines explicitly compare their recommendations."""
