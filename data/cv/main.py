import os
import argparse
import fitz  # PyMuPDF
import google.generativeai as genai
import pandas as pd
import json


# Configure Gemini API
GEMINI_API_KEY = "AIzaSyAB2xeYE1JQ1T02X-jp5ESFjFATGyHheYU"
genai.configure(api_key=GEMINI_API_KEY)

def extract_text_from_pdf(pdf_path):
    """Trích xuất văn bản từ file PDF."""
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    except Exception as e:
        print(f"Lỗi khi trích xuất PDF: {e}")
        return None

def analyze_cv(cv_text):
    """Phân tích CV bằng Gemini API."""
    model = genai.GenerativeModel('gemini-1.5-pro')
    
    prompt = f"""
    Bạn là một chuyên gia đánh giá CV cao cấp với hơn 15 năm kinh nghiệm trong lĩnh vực tuyển dụng và phát triển nhân sự. Hãy phân tích CV sau đây một cách CHI TIẾT và ĐẦY ĐỦ NHẤT, đánh giá theo các tiêu chí:
    
    1. Thông tin cá nhân: Đánh giá mức độ đầy đủ, rõ ràng và chuyên nghiệp của thông tin liên hệ. Đánh giá xem thông tin cá nhân có phù hợp với các tiêu chuẩn tuyển dụng hiện đại không, có các thông tin quan trọng như email, số điện thoại, LinkedIn, địa chỉ, và có gây ấn tượng với nhà tuyển dụng hay không.
    
    2. Trình độ học vấn: Đánh giá chi tiết về sự phù hợp và cách trình bày thông tin học vấn. Đánh giá xem trình độ học vấn có liên quan đến vị trí đang ứng tuyển không, cách trình bày các thành tích học tập, chứng chỉ, khóa học, và sự nhất quán của thông tin này.
    
    3. Kinh nghiệm làm việc: Đánh giá chi tiết về cách mô tả kinh nghiệm, thành tựu và trách nhiệm. Đánh giá về độ dài, tính cụ thể, sử dụng từ ngữ hành động, trình bày thành tựu có lượng hóa được, sự liên quan đến vị trí đang ứng tuyển, và cách trình bày tiến trình nghề nghiệp.
    
    4. Kỹ năng: Đánh giá chi tiết về sự phù hợp của kỹ năng với ngành nghề, phân biệt giữa kỹ năng cứng và kỹ năng mềm. Đánh giá sự cân đối giữa các loại kỹ năng, mức độ phù hợp với vị trí, sự hiện đại và cập nhật của các kỹ năng, cách trình bày và phân loại kỹ năng.
    
    5. Dự án/Portfolio: Đánh giá chi tiết về cách trình bày và mức độ liên quan của các dự án. Đánh giá về cách mô tả dự án, kết quả cụ thể đạt được, kỹ năng thể hiện trong từng dự án, quy mô và tác động của dự án, cách thể hiện vai trò cá nhân trong dự án nhóm.
    
    6. Cấu trúc và định dạng: Đánh giá chi tiết về tính rõ ràng, nhất quán và chuyên nghiệp của CV. Đánh giá về bố cục, font chữ, màu sắc, khoảng cách, sự cân đối, và mức độ dễ đọc. Phân tích xem CV có tuân theo các tiêu chuẩn ngành không và có phù hợp với văn hóa công ty mục tiêu không.
    
    7. Ngôn ngữ và cách diễn đạt: Đánh giá chi tiết về ngữ pháp, chính tả, tính mạch lạc và chuyên nghiệp trong cách diễn đạt. Đánh giá về việc sử dụng từ ngữ chuyên ngành, tính nhất quán của thì động từ, mức độ súc tích, và hiệu quả của các động từ hành động.
    
    Cho mỗi tiêu chí, hãy đánh giá theo thang điểm từ 1-10, với:
    - 1-3: Cần cải thiện nhiều (Phân tích chi tiết tại sao)
    - 4-6: Trung bình (Phân tích chi tiết tại sao)
    - 7-8: Tốt (Phân tích chi tiết tại sao)
    - 9-10: Xuất sắc (Phân tích chi tiết tại sao)
    
    Trả về kết quả phân tích dưới dạng JSON với cấu trúc sau:
    {{
        "thong_tin_ca_nhan": {{
            "diem": <điểm số>,
            "nhan_xet": "<nhận xét chi tiết, ít nhất 300 từ>",
            "de_xuat": "<đề xuất cải thiện chi tiết, ít nhất 200 từ>"
        }},
        "trinh_do_hoc_van": {{
            "diem": <điểm số>,
            "nhan_xet": "<nhận xét chi tiết, ít nhất 300 từ>",
            "de_xuat": "<đề xuất cải thiện chi tiết, ít nhất 200 từ>"
        }},
        "kinh_nghiem_lam_viec": {{
            "diem": <điểm số>,
            "nhan_xet": "<nhận xét chi tiết, ít nhất 300 từ>",
            "de_xuat": "<đề xuất cải thiện chi tiết, ít nhất 200 từ>"
        }},
        "ky_nang": {{
            "diem": <điểm số>,
            "nhan_xet": "<nhận xét chi tiết, ít nhất 300 từ>",
            "de_xuat": "<đề xuất cải thiện chi tiết, ít nhất 200 từ>"
        }},
        "du_an_portfolio": {{
            "diem": <điểm số>,
            "nhan_xet": "<nhận xét chi tiết, ít nhất 300 từ>",
            "de_xuat": "<đề xuất cải thiện chi tiết, ít nhất 200 từ>"
        }},
        "cau_truc_va_dinh_dang": {{
            "diem": <điểm số>,
            "nhan_xet": "<nhận xét chi tiết, ít nhất 300 từ>",
            "de_xuat": "<đề xuất cải thiện chi tiết, ít nhất 200 từ>"
        }},
        "ngon_ngu_va_cach_dien_dat": {{
            "diem": <điểm số>,
            "nhan_xet": "<nhận xét chi tiết, ít nhất 300 từ>",
            "de_xuat": "<đề xuất cải thiện chi tiết, ít nhất 200 từ>"
        }},
        "danh_gia_tong_the": {{
            "diem_trung_binh": <điểm trung bình>,
            "danh_gia_chi_tiet": "<một đoạn dài ít nhất 500 từ phân tích tổng thể CV, đánh giá chi tiết các điểm mạnh, điểm yếu, mức độ phù hợp với thị trường việc làm hiện tại, triển vọng nghề nghiệp, và điểm nổi bật so với các ứng viên cùng ngành>",
            "diem_manh": ["<điểm mạnh 1 - chi tiết>", "<điểm mạnh 2 - chi tiết>", "<điểm mạnh 3 - chi tiết>", "<điểm mạnh 4 - chi tiết>", "<điểm mạnh 5 - chi tiết>"],
            "diem_yeu": ["<điểm yếu 1 - chi tiết>", "<điểm yếu 2 - chi tiết>", "<điểm yếu 3 - chi tiết>", "<điểm yếu 4 - chi tiết>", "<điểm yếu 5 - chi tiết>"],
            "de_xuat_cai_thien": ["<đề xuất 1 - chi tiết>", "<đề xuất 2 - chi tiết>", "<đề xuất 3 - chi tiết>", "<đề xuất 4 - chi tiết>", "<đề xuất 5 - chi tiết>", "<đề xuất 6 - chi tiết>", "<đề xuất 7 - chi tiết>"],
            "nhan_xet_chung": "<nhận xét tổng thể chi tiết ít nhất 300 từ>",
            "tac_dong_thi_truong": "<phân tích chi tiết ít nhất 300 từ về cách CV này sẽ được nhìn nhận trên thị trường lao động hiện tại, tỷ lệ thành công và các khuyến nghị cụ thể để tăng tỷ lệ được phỏng vấn>"
        }},
        "nganh_nghe_phu_hop": ["<ngành nghề 1 - với giải thích chi tiết>", "<ngành nghề 2 - với giải thích chi tiết>", "<ngành nghề 3 - với giải thích chi tiết>", "<ngành nghề 4 - với giải thích chi tiết>", "<ngành nghề 5 - với giải thích chi tiết>"],
        "phan_tich_xu_huong": "<phân tích chi tiết ít nhất 400 từ về sự phù hợp của CV này với xu hướng tuyển dụng hiện tại và tương lai, các kỹ năng đang được ưa chuộng và các xu hướng ngành nghề>"
    }}
    
    Đây là nội dung CV:
    
    {cv_text}
    """
    
    try:
        response = model.generate_content(prompt)
        # Parse JSON từ phản hồi
        try:
            result = json.loads(response.text)
            return result
        except json.JSONDecodeError:
            # Nếu không phân tích được JSON, trả về văn bản gốc
            return {"error": "Done", "raw_response": response.text}
    except Exception as e:
        return {"error": f"Lỗi khi sử dụng Gemini API: {str(e)}"}

def format_cv_analysis(analysis):
    """Định dạng kết quả phân tích CV thành văn bản dễ đọc."""
    if "error" in analysis:
        return f"Output: {analysis['error']}\n\nPhản hồi gốc: {analysis.get('raw_response', 'Không có')}"
    
    output = "====================================\n"
    output += "=== PHÂN TÍCH CHI TIẾT CV ===\n"
    output += "====================================\n\n"
    
    # Thông tin từng tiêu chí
    categories = [
        "thong_tin_ca_nhan", "trinh_do_hoc_van", "kinh_nghiem_lam_viec", 
        "ky_nang", "du_an_portfolio", "cau_truc_va_dinh_dang", 
        "ngon_ngu_va_cach_dien_dat"
    ]
    
    category_names = {
        "thong_tin_ca_nhan": "THÔNG TIN CÁ NHÂN",
        "trinh_do_hoc_van": "TRÌNH ĐỘ HỌC VẤN",
        "kinh_nghiem_lam_viec": "KINH NGHIỆM LÀM VIỆC",
        "ky_nang": "KỸ NĂNG",
        "du_an_portfolio": "DỰ ÁN/PORTFOLIO",
        "cau_truc_va_dinh_dang": "CẤU TRÚC VÀ ĐỊNH DẠNG",
        "ngon_ngu_va_cach_dien_dat": "NGÔN NGỮ VÀ CÁCH DIỄN ĐẠT"
    }
    
    for category in categories:
        if category in analysis:
            cat_data = analysis[category]
            output += f"## {category_names[category]}\n"
            output += f"Điểm số: {cat_data['diem']}/10\n"
            output += "---------------------------------------\n"
            output += "### Nhận xét chi tiết:\n"
            output += f"{cat_data['nhan_xet']}\n\n"
            output += "### Đề xuất cải thiện:\n"
            output += f"{cat_data['de_xuat']}\n\n"
            output += "=======================================\n\n"
    
    # Đánh giá tổng thể
    if "danh_gia_tong_the" in analysis:
        total = analysis["danh_gia_tong_the"]
        output += "## ĐÁNH GIÁ TỔNG THỂ\n"
        output += f"Điểm trung bình: {total['diem_trung_binh']}/10\n"
        output += "---------------------------------------\n\n"
        
        if "danh_gia_chi_tiet" in total:
            output += "### Phân tích tổng thể:\n"
            output += f"{total['danh_gia_chi_tiet']}\n\n"
        
        output += "### Điểm mạnh:\n"
        for strength in total['diem_manh']:
            output += f"- {strength}\n"
        
        output += "\n### Điểm yếu:\n"
        for weakness in total['diem_yeu']:
            output += f"- {weakness}\n"
        
        output += "\n### Đề xuất cải thiện:\n"
        for suggestion in total['de_xuat_cai_thien']:
            output += f"- {suggestion}\n"
        
        output += f"\n### Nhận xét chung:\n{total['nhan_xet_chung']}\n\n"
        
        if "tac_dong_thi_truong" in total:
            output += "### Tác động trên thị trường lao động:\n"
            output += f"{total['tac_dong_thi_truong']}\n\n"
    
    # Ngành nghề phù hợp
    if "nganh_nghe_phu_hop" in analysis:
        output += "## NGÀNH NGHỀ PHÙ HỢP\n"
        output += "---------------------------------------\n"
        for job in analysis["nganh_nghe_phu_hop"]:
            output += f"- {job}\n"
        output += "\n"
    
    # Phân tích xu hướng
    if "phan_tich_xu_huong" in analysis:
        output += "## PHÂN TÍCH XU HƯỚNG THỊ TRƯỜNG\n"
        output += "---------------------------------------\n"
        output += f"{analysis['phan_tich_xu_huong']}\n\n"
    
    output += "====================================\n"
    output += "= KẾT THÚC BÁO CÁO PHÂN TÍCH CV =\n"
    output += "====================================\n"
    
    return output

def main():
    parser = argparse.ArgumentParser(description='Phân tích CV bằng Gemini API')
    parser.add_argument('pdf_path', help='Đường dẫn đến file CV (PDF)')
    parser.add_argument('--excel', help='Đường dẫn lưu file Excel kết quả', default='cv_analysis.xlsx')
    parser.add_argument('--text', help='Đường dẫn lưu file text kết quả', default='cv_analysis.txt')
    args = parser.parse_args()
    
    # Kiểm tra file tồn tại
    if not os.path.exists(args.pdf_path):
        print(f"Lỗi: File {args.pdf_path} không tồn tại!")
        return
    
    # Kiểm tra API key
    if not GEMINI_API_KEY:
        print("Lỗi: Không tìm thấy GEMINI_API_KEY trong biến môi trường!")
        print("Vui lòng tạo file .env chứa GEMINI_API_KEY=your_api_key")
        return
    
    print(f"Đang phân tích CV từ file: {args.pdf_path}")
    
    # Trích xuất văn bản từ PDF
    cv_text = extract_text_from_pdf(args.pdf_path)
    if not cv_text:
        print("Không thể trích xuất nội dung từ PDF.")
        return
    
    # Phân tích CV
    print("Đang gửi CV đến Gemini API để phân tích...")
    analysis = analyze_cv(cv_text)
    
    # Định dạng kết quả
    formatted_analysis = format_cv_analysis(analysis)
    
    # Lưu kết quả vào file
    with open(args.text, 'w', encoding='utf-8') as f:
        f.write(formatted_analysis)
    print(f"Đã lưu kết quả phân tích văn bản vào: {args.text}")
    
    # In kết quả ra màn hình
    print("\n" + "="*50)
    print(formatted_analysis)
    print("="*50)

if __name__ == "__main__":
    main()