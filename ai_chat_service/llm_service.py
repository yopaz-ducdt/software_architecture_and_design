import os
from typing import Any
from dotenv import load_dotenv
from groq import Groq

# Load .env file
load_dotenv()

class LLMService:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        if self.api_key:
            self.client = Groq(api_key=self.api_key)
        else:
            self.client = None
        self.model_name = "llama-3.3-70b-versatile"

    def build_prompt(
        self,
        user_name: str,
        question: str,
        behavior: dict,
        products: list[dict],
        kb_docs: list[str],
        dynamic_context: str = ""
    ) -> str:
        prompt = f"""Bạn là trợ lý ảo thân thiện của một cửa hàng trực tuyến (Shop Trung Đức) chuyên bán Đồ dùng học tập, Sách, Quà tặng, Đồ chơi, và Phụ kiện công nghệ.
Nhiệm vụ của bạn là tư vấn cho khách hàng tên là '{user_name}'.

THÔNG TIN NGƯỜI DÙNG HIỆN TẠI (Dùng để hiểu sở thích và cách xưng hô/tư vấn):
- Phân khúc khách hàng (Persona): {behavior.get('persona', 'N/A')}
- Độ nhạy cảm với giá: {behavior.get('price_sensitivity', 'N/A')}

CHÍNH SÁCH VÀ HƯỚNG DẪN TỪ CỬA HÀNG (KNOWLEDGE BASE):
{chr(10).join([f"- {doc}" for doc in kb_docs]) if kb_docs else "Không có thông tin nội bộ liên quan."}

SẢN PHẨM GỢI Ý (Đã được hệ thống AI nội bộ chọn lọc phù hợp nhất):
"""
        if not products:
            prompt += "Không có sản phẩm nào khớp với tìm kiếm hiện tại.\n"
        for i, p in enumerate(products, 1):
            title = p.get('title') or p.get('name') or 'Sản phẩm'
            price = p.get('price', 0)
            desc = p.get('description', '')
            prompt += f"{i}. {title} - Giá: {int(float(price)):,}đ\n   Mô tả: {desc}\n"
        
        prompt += f"""
NGỮ CẢNH BỔ SUNG:
{dynamic_context if dynamic_context else "Không có."}

YÊU CẦU:
- Khách hàng đang nói: "{question}"
- Hãy đóng vai nhân viên tư vấn, trả lời tự nhiên, thân thiện và có sự thấu cảm (nếu khách buồn/vui). Dùng emoji hợp lý.
- Dựa vào những "Sản phẩm gợi ý" để khuyên khách, tuyệt đối KHÔNG tự bịa ra (hallucinate) sản phẩm ngoài danh sách.
- Không cần in lại nguyên văn danh sách sản phẩm như một cái menu, hãy lồng ghép khéo léo vào câu trả lời tư vấn. Nếu có 3 sản phẩm, hãy nói chung chung hoặc làm nổi bật sản phẩm phù hợp nhất.
- Trả lời thẳng vào vấn đề khách hỏi, không dài dòng lê thê bằng tiếng Việt.
"""
        return prompt

    def generate_answer(self, prompt: str) -> str:
        if not self.client:
            return "Xin lỗi, hệ thống chưa được cấu hình LLM API Key (GROQ_API_KEY chưa có)."
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1024,
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"LLM Error: {e}")
            return f"Xin lỗi, mình đang gặp chút trục trặc mạng ({str(e)[:50]}...). Bạn thông cảm thử lại nhé!"
